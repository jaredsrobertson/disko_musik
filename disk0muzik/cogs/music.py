import logging
import discord
import asyncio
from discord.ext import commands
from discord import FFmpegPCMAudio
from disk0muzik.utils.spotify_helper import search_spotify
from disk0muzik.utils.yt_dlp_helper import extract_youtube_info
from disk0muzik.utils.embed_helper import (
    create_now_playing_embed,
    create_paused_embed,
    create_queued_embed,
    create_played_embed,
)
from disk0muzik.utils.database import add_song, get_random_song
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class GuildMusicState:
    def __init__(self) -> None:
        self.voice_client: Optional[discord.VoiceClient] = None
        self.queue: List[Dict[str, str]] = []
        self.current_song: Optional[Dict[str, str]] = None
        self.is_paused: bool = False
        self.now_playing_message: Optional[discord.Message] = None
        self.skip_event = asyncio.Event()
        self.lock = asyncio.Lock()


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.guild_states: Dict[int, GuildMusicState] = {}
        logger.info("Music cog initialized.")

    def get_guild_state(self, guild_id: int) -> GuildMusicState:
        return self.guild_states.setdefault(guild_id, GuildMusicState())

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author != self.bot.user and message.content.startswith("."):
            query = message.content[1:].strip()
            logger.info(f"Processing song request: {query}")
            await self.handle_song_request(message, query)
            await message.delete()

    async def join_voice_channel(
        self, message: discord.Message, guild_state: GuildMusicState
    ) -> None:
        if message.author.voice:
            channel = message.author.voice.channel
            guild_state.voice_client = await channel.connect()
            logger.info(f"Joined voice channel: {channel}")
        else:
            await message.channel.send(
                "You need to be in a voice channel to request a song."
            )
            logger.warning("User is not in a voice channel.")

    async def handle_song_request(self, message: discord.Message, query: str) -> None:
        guild_state = self.get_guild_state(message.guild.id)

        try:
            if (
                guild_state.voice_client is None
                or not guild_state.voice_client.is_connected()
            ):
                await self.join_voice_channel(message, guild_state)

            song = await self.process_song_query(query, message.author.display_name)

            if not song:
                await message.channel.send(
                    "An error occurred while processing your request."
                )
                return

            async with guild_state.lock:
                if (
                    guild_state.current_song
                    or guild_state.voice_client.is_playing()
                    or guild_state.is_paused
                ):
                    guild_state.queue.append(song)
                    embed, view = create_queued_embed(song, song["requester"])
                    song["message"] = await message.channel.send(embed=embed, view=view)
                    logger.info(f"Queued song: {song['title']}")
                    play_immediately = False
                else:
                    play_immediately = True

            # Call play_song outside the lock
            if play_immediately:
                await self.play_song(message.channel, song, guild_state)

        except Exception as e:
            logger.error(f"Error handling song request: {e}")
            await message.channel.send(
                "An error occurred while processing your request."
            )

    async def process_song_query(
        self, query: str, requester: str
    ) -> Optional[Dict[str, str]]:
        try:
            if "youtube.com" in query or "youtu.be" in query:
                video_info = await asyncio.to_thread(extract_youtube_info, query)
                if not video_info:
                    return None

                spotify_result = await asyncio.to_thread(
                    search_spotify, video_info["title"]
                )
                if not spotify_result:
                    return None

                song = {
                    "spotify_id": spotify_result["spotify_id"],
                    "title": spotify_result["title"],
                    "artist": spotify_result["artist"],
                    "thumbnail": spotify_result["album_art"],
                    "youtube_url": video_info["video_url"],
                    "requester": requester,
                }
            else:
                spotify_result = await asyncio.to_thread(search_spotify, query)
                if not spotify_result:
                    return None

                youtube_info = await asyncio.to_thread(
                    extract_youtube_info,
                    f"{spotify_result['artist']} {spotify_result['title']}",
                )
                if not youtube_info:
                    return None

                song = {
                    "spotify_id": spotify_result["spotify_id"],
                    "title": spotify_result["title"],
                    "artist": spotify_result["artist"],
                    "thumbnail": spotify_result["album_art"],
                    "youtube_url": youtube_info["video_url"],
                    "requester": requester,
                }

            return song

        except Exception as e:
            logger.error(f"Error processing song query: {e}")
            return None

    async def play_song(
        self,
        channel: discord.TextChannel,
        song: Dict[str, str],
        guild_state: GuildMusicState,
    ) -> None:
        guild_state.current_song = song
        guild_state.is_paused = False
        guild_state.skip_event.clear()
        logger.info(f"Playing song: {song['title']}")

        FFMPEG_OPTIONS = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }

        try:
            video_info = await asyncio.to_thread(
                extract_youtube_info, song["youtube_url"]
            )
            audio_url = video_info["audio_url"]

            guild_state.voice_client.play(
                FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS),
                after=lambda e: self.bot.loop.call_soon_threadsafe(
                    guild_state.skip_event.set
                ),
            )

            embed, view = create_now_playing_embed(song, song["requester"], "❚❚")
            guild_state.now_playing_message = await (
                song.get("message").edit(embed=embed, view=view)
                if song.get("message")
                else channel.send(embed=embed, view=view)
            )
            song["message"] = guild_state.now_playing_message

        except Exception as e:
            logger.error(f"Error playing song: {e}")
            await channel.send("An error occurred while playing the song.")
            return

        await guild_state.skip_event.wait()
        await self.handle_song_finished(channel, guild_state)

    async def handle_song_finished(
        self, channel: discord.TextChannel, guild_state: GuildMusicState
    ) -> None:
        logger.info(f"Song finished: {guild_state.current_song}")
        if guild_state.current_song:
            embed = create_played_embed(
                guild_state.current_song, guild_state.current_song["requester"]
            )
            if guild_state.now_playing_message:
                await guild_state.now_playing_message.edit(embed=embed, view=None)
            add_song(guild_state.current_song)
            guild_state.current_song = None

        next_song = None
        async with guild_state.lock:
            if guild_state.queue:
                next_song = guild_state.queue.pop(0)
                logger.info(f"Next song from queue: {next_song['title']}")

        if next_song:
            await self.play_song(channel, next_song, guild_state)
        else:
            logger.info("Queue is empty, playing a random song from the database.")
            db_song = get_random_song()
            if db_song:
                db_song["message"] = None
                await self.play_song(channel, db_song, guild_state)

    async def handle_button_click(self, interaction: discord.Interaction) -> None:
        guild_state = self.get_guild_state(interaction.guild_id)

        button_id = interaction.data.get("custom_id")
        logger.info(f"Button clicked: {button_id}")

        if guild_state.current_song and button_id == "play_pause_button":
            if guild_state.voice_client.is_playing():
                guild_state.voice_client.pause()
                guild_state.is_paused = True
                embed, view = create_paused_embed(
                    guild_state.current_song, guild_state.current_song["requester"]
                )
                await guild_state.now_playing_message.edit(embed=embed, view=view)
                logger.info("Paused song.")
            elif guild_state.is_paused:
                guild_state.voice_client.resume()
                guild_state.is_paused = False
                embed, view = create_now_playing_embed(
                    guild_state.current_song,
                    guild_state.current_song["requester"],
                    "❚❚",
                )
                await guild_state.now_playing_message.edit(embed=embed, view=view)
                logger.info("Resumed song.")
        elif guild_state.current_song and button_id == "skip_button":
            if guild_state.voice_client.is_playing() or guild_state.is_paused:
                guild_state.voice_client.stop()
                guild_state.is_paused = False
                guild_state.skip_event.set()
                logger.info("Skipped song.")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        if interaction.type == discord.InteractionType.component:
            await interaction.response.defer()
            await self.handle_button_click(interaction)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot))
    logger.info("Music cog added to bot.")
