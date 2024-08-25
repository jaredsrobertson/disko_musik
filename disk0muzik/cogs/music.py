import logging
import discord
from discord.ext import commands
from disk0muzik.state.guild_music_state import GuildMusicState
from disk0muzik.utils.song_processing import process_song_query
from disk0muzik.utils.voice_channel import join_voice_channel
from disk0muzik.utils.song_playback import play_song
from disk0muzik.utils.interaction_handler import on_interaction
from disk0muzik.utils.embed_helper import create_queued_embed
from typing import Dict

logger = logging.getLogger(__name__)


class Music(commands.Cog):
    """
    Cog that handles music-related commands and events, including song requests,
    song playback, and interaction with voice channels.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Initializes the Music cog with the bot instance and sets up guild states.

        :param bot: The bot instance.
        """
        self.bot = bot
        self.guild_states: Dict[int, GuildMusicState] = {}
        logger.info("Music cog initialized.")

    def get_guild_state(self, guild_id: int) -> GuildMusicState:
        """
        Retrieves the GuildMusicState for a given guild. If none exists, it creates a new one.

        :param guild_id: The ID of the guild.
        :return: The GuildMusicState instance for the guild.
        """
        if guild_id not in self.guild_states:
            self.guild_states[guild_id] = GuildMusicState()
        return self.guild_states[guild_id]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        Listens for messages to handle song requests prefixed with '.'.

        :param message: The received Discord message.
        """
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

    async def handle_song_request(self, message: discord.Message, query: str) -> None:
        """
        Processes a song request, either queuing it or playing it immediately.

        :param message: The message containing the song request.
        :param query: The query for the song to be played.
        """
        guild_id = message.guild.id
        guild_state = self.get_guild_state(guild_id)

        try:
            if (
                guild_state.voice_client is None
                or not guild_state.voice_client.is_connected()
            ):
                await join_voice_channel(message, guild_state)

            song = await process_song_query(
                query, message.author.display_name, message.author.id
            )

            if not song:
                await message.channel.send(
                    "An error occurred while processing your request."
                )
                return

            play_immediately = False
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
                else:
                    play_immediately = True

            if play_immediately:
                await play_song(message.channel, song, guild_state)

        except Exception as e:
            logger.error(f"Error handling song request: {e}")
            await message.channel.send(
                "An error occurred while processing your request."
            )

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        """
        Handles Discord interactions (e.g., button clicks) related to the music commands.

        :param interaction: The interaction event from Discord.
        """
        await on_interaction(interaction, self.get_guild_state)


async def setup(bot: commands.Bot) -> None:
    """
    Adds the Music cog to the bot instance.

    :param bot: The bot instance.
    """
    await bot.add_cog(Music(bot))
    logger.info("Music cog added to bot.")
