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


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.voice_client: Optional[discord.VoiceClient] = None
        self.queue: List[Dict[str, str]] = []
        self.current_song: Optional[Dict[str, str]] = None
        self.is_paused: bool = False
        self.now_playing_message: Optional[discord.Message] = None
        self.skip_event = asyncio.Event()
        self.lock = asyncio.Lock()
        logger.info("Music cog initialized.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.bot.user:
            return

        if message.content.startswith("."):
            query = message.content[1:].strip()
            logger.info(f"Processing song request: {query}")
            try:
                await message.delete()
            except Exception as e:
                logger.error(f"Failed to delete message: {e}")
            await self.handle_song_request(message, query)

    async def join_voice_channel(self, message: discord.Message) -> None:
        if not message.author.voice:
            await message.channel.send(
                "You need to be in a voice channel to request a song."
            )
            logger.warning("User is not in a voice channel.")
            return

        channel = message.author.voice.channel
        self.voice_client = await channel.connect()
        logger.info(f"Joined voice channel: {channel}")

    async def handle_song_request(self, message: discord.Message, query: str) -> None:
        try:
            # Join the voice channel if not already connected
            if self.voice_client is None or not self.voice_client.is_connected():
                await self.join_voice_channel(message)

            # Process the song request
            song = await self.process_song_query(query, message.author.display_name)

            if not song:
                await message.channel.send(
                    "An error occurred while processing your request."
                )
                return

            # Determine whether to queue the song or play it immediately
            play_immediately = False
            async with self.lock:
                if (
                    self.current_song
                    or self.voice_client.is_playing()
                    or self.is_paused
                ):
                    self.queue.append(song)
                    embed, view = create_queued_embed(song, song["requester"])
                    song["message"] = await message.channel.send(embed=embed, view=view)
                    logger.info(f"Queued song: {song['title']}")
                else:
                    play_immediately = True

            # Play the song if no other song is currently playing
            if play_immediately:
                await self.play_song(message.channel, song)

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
                logger.info(f"Processing YouTube URL: {query}")
                video_info = await asyncio.to_thread(extract_youtube_info, query)
                if not video_info:
                    logger.error("Couldn't extract video info from YouTube URL.")
                    return None

                spotify_result = await asyncio.to_thread(
                    search_spotify, video_info["title"]
                )
                if not spotify_result:
                    logger.error("Couldn't find the song on Spotify.")
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
                logger.info(f"Searching Spotify for query: {query}")
                spotify_result = await asyncio.to_thread(search_spotify, query)
                if not spotify_result:
                    logger.error("Couldn't find the song on Spotify.")
                    return None

                youtube_info = await asyncio.to_thread(
                    extract_youtube_info,
                    f"{spotify_result['artist']} {spotify_result['title']}",
                )
                if not youtube_info:
                    logger.error("Couldn't find the song on YouTube.")
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
        self, channel: discord.TextChannel, song: Dict[str, str]
    ) -> None:
        if song is None:
            logger.error("Cannot play an undefined song.")
            return

        self.current_song = song
        self.is_paused = False
        self.skip_event.clear()
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
            logger.info(f"Audio URL: {audio_url}")

            self.voice_client.play(
                FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS),
                after=lambda e: self.bot.loop.call_soon_threadsafe(self.skip_event.set),
            )
            embed, view = create_now_playing_embed(song, song["requester"], "❚❚")
            self.now_playing_message = await (
                song.get("message").edit(embed=embed, view=view)
                if song.get("message")
                else channel.send(embed=embed, view=view)
            )
            song["message"] = self.now_playing_message
        except Exception as e:
            logger.error(f"Error playing song: {e}")
            await channel.send("An error occurred while playing the song.")

        await self.skip_event.wait()
        await self.handle_song_finished(channel)

    async def handle_song_finished(self, channel: discord.TextChannel) -> None:
        logger.info(f"Song finished: {self.current_song}")
        if self.current_song:
            embed = create_played_embed(
                self.current_song, self.current_song["requester"]
            )
            if self.now_playing_message:
                await self.now_playing_message.edit(embed=embed, view=None)
            add_song(self.current_song)
            self.current_song = None

        next_song = None
        async with self.lock:
            if self.queue:
                next_song = self.queue.pop(0)
                logger.info(f"Next song from queue: {next_song['title']}")

        if next_song:
            await self.play_song(channel, next_song)
        else:
            logger.info("Queue is empty, playing a random song from the database.")
            db_song = get_random_song()
            if db_song:
                db_song["message"] = None
                await self.play_song(channel, db_song)

    async def handle_button_click(self, interaction: discord.Interaction) -> None:
        button_id = interaction.data.get("custom_id")
        logger.info(f"Button clicked: {button_id}")
        if self.current_song and button_id == "play_pause_button":
            if self.voice_client.is_playing():
                self.voice_client.pause()
                self.is_paused = True
                embed, view = create_paused_embed(
                    self.current_song, self.current_song["requester"]
                )
                await self.now_playing_message.edit(embed=embed, view=view)
                logger.info("Paused song.")
            elif self.is_paused:
                self.voice_client.resume()
                self.is_paused = False
                embed, view = create_now_playing_embed(
                    self.current_song, self.current_song["requester"], "❚❚"
                )
                await self.now_playing_message.edit(embed=embed, view=view)
                logger.info("Resumed song.")
        elif self.current_song and button_id == "skip_button":
            if self.voice_client.is_playing() or self.is_paused:
                self.voice_client.stop()
                self.is_paused = False
                self.skip_event.set()
                logger.info("Skipped song.")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        logger.info(f"Interaction received: {interaction.data.get('custom_id')}")
        if interaction.type == discord.InteractionType.component:
            await interaction.response.defer()
            await self.handle_button_click(interaction)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot))
    logger.info("Music cog added to bot.")
