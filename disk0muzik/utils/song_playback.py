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
)

logger = logging.getLogger(__name__)


async def play_song(
    channel: discord.TextChannel,
    song: Dict[str, str],
    guild_state: GuildMusicState,
) -> None:
    if song is None:
        logger.error("Cannot play an undefined song.")
        return

    guild_state.current_song = song
    guild_state.is_paused = False
    guild_state.skip_event.clear()
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
        await play_song(channel, next_song, guild_state)
    else:
        logger.info("Queue is empty, playing a random song from the database.")
        db_song = get_random_song()
        if db_song:
            db_song["message"] = None
            await play_song(channel, db_song, guild_state)
