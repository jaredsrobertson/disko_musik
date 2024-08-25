import logging
import discord
from disk0muzik.state.guild_music_state import GuildMusicState

logger = logging.getLogger(__name__)

async def join_voice_channel(
    message: discord.Message, guild_state: GuildMusicState
) -> None:
    """
    Joins the voice channel of the user who requested a song.

    Args:
        message (discord.Message): The message object representing the user's request.
        guild_state (GuildMusicState): The state of the guild's music session.

    Returns:
        None
    """
    if not message.author.voice:
        await message.channel.send(
            "You need to be in a voice channel to request a song."
        )
        logger.warning("User is not in a voice channel.")
        return

    channel = message.author.voice.channel
    guild_state.voice_client = await channel.connect()
    logger.info(f"Joined voice channel: {channel}")
