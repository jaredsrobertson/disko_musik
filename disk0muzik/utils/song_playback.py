import logging
import asyncio
import discord
from discord import FFmpegPCMAudio
from typing import Dict
from disk0muzik.state.guild_music_state import GuildMusicState
from disk0muzik.utils.yt_dlp_helper import extract_youtube_info
from disk0muzik.utils.database import add_song, get_random_song
from disk0muzik.utils.embed_helper import (
    create_now_playing_embed,
    create_played_embed,
    create_paused_embed,
)

logger = logging.getLogger(__name__)

async def play_song(
    channel: discord.TextChannel,
    song: Dict[str, str],
    guild_state: GuildMusicState,
) -> None:
    """
    Plays a song in the voice channel and manages the playback state.

    :param channel: The text channel where the now playing message will be sent.
    :param song: The song to be played.
    :param guild_state: The current guild's music state.
    """
    if song is None:
        logger.error("Cannot play an undefined song.")
        return

    song["requester_id"] = song.get(
        "requester_id",
        guild_state.current_song.get("requester_id") if guild_state.current_song else None,
    )

    guild_state.current_song = song
    guild_state.is_paused = False
    guild_state.skip_event.clear()
    guild_state.reset_votes()

    logger.info(f"Playing song: {song['title']}")

    FFMPEG_OPTIONS = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn",
    }

    try:
        video_info = await asyncio.to_thread(extract_youtube_info, song["youtube_url"])
        audio_url = video_info["audio_url"]
        logger.info(f"Audio URL: {audio_url}")

        guild_state.voice_client.play(
            FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS),
            after=lambda e: guild_state.skip_event.set(),
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
    await handle_song_finished(channel, guild_state)

async def handle_song_finished(
    channel: discord.TextChannel, guild_state: GuildMusicState
) -> None:
    """
    Handles the cleanup after a song finishes playing and queues the next song.

    :param channel: The text channel where the now playing message was sent.
    :param guild_state: The current guild's music state.
    """
    logger.info(f"Song finished: {guild_state.current_song}")
    if guild_state.current_song:
        embed = create_played_embed(guild_state.current_song, guild_state.current_song["requester"])
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
        await play_song(channel, next_song, guild_state)
    else:
        logger.info("Queue is empty, playing a random song from the database.")
        db_song = get_random_song()
        if db_song:
            db_song["message"] = None
            await play_song(channel, db_song, guild_state)

async def handle_skip_vote(
    interaction: discord.Interaction, guild_state: GuildMusicState
) -> None:
    """
    Handles the skip vote from a user and checks if the skip threshold is reached.

    :param interaction: The interaction object representing the vote.
    :param guild_state: The current guild's music state.
    """
    user_id = interaction.user.id

    if user_id == guild_state.current_song["requester_id"]:
        guild_state.skip_event.set()
        return

    guild_state.add_skip_vote(user_id)

    skip_reaction = "⏭️"
    await guild_state.now_playing_message.add_reaction(skip_reaction)

    if len(guild_state.skip_votes) >= 2:
        guild_state.skip_event.set()

async def handle_pause_vote(
    interaction: discord.Interaction, guild_state: GuildMusicState
) -> None:
    """
    Handles the pause vote from a user and checks if the pause threshold is reached.

    :param interaction: The interaction object representing the vote.
    :param guild_state: The current guild's music state.
    """
    user_id = interaction.user.id

    if user_id == guild_state.current_song["requester_id"]:
        if guild_state.voice_client.is_playing():
            guild_state.voice_client.pause()
            guild_state.is_paused = True
            embed, view = create_paused_embed(
                guild_state.current_song,
                guild_state.current_song["requester"],
            )
            await guild_state.now_playing_message.edit(embed=embed, view=view)
        return

    guild_state.add_pause_vote(user_id)

    pause_reaction = "⏸️"
    await guild_state.now_playing_message.add_reaction(pause_reaction)

    if len(guild_state.pause_votes) >= 2:
        if guild_state.voice_client.is_playing():
            guild_state.voice_client.pause()
            guild_state.is_paused = True
            embed, view = create_paused_embed(
                guild_state.current_song,
                guild_state.current_song["requester"],
            )
            await guild_state.now_playing_message.edit(embed=embed, view=view)
