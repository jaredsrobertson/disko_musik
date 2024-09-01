import logging
import asyncio
import discord
from discord import FFmpegPCMAudio
from typing import Dict
from disk0muzik.state.guild_music_state import GuildMusicState
from disk0muzik.utils.yt_dlp_helper import extract_youtube_info
from disk0muzik.utils.database import add_song
from disk0muzik.utils.embed_helper import (
    create_now_playing_embed,
    create_played_embed,
    create_paused_embed,
    create_now_playing_from_playlist_embed,
    create_played_from_playlist_embed,
    create_skipped_embed,
    create_skipped_from_playlist_embed,
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
        "requester_id", guild_state.current_song.get("requester_id") if guild_state.current_song else None
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
        # Check if the youtube_url is reachable
        video_info = await asyncio.to_thread(extract_youtube_info, song["youtube_url"])
        audio_url = video_info["audio_url"]
        logger.info(f"Audio URL: {audio_url}")

    except Exception as e:
        # If the youtube_url fails, search for a new one
        logger.error(f"Error with youtube_url, searching for a new one: {e}")
        try:
            video_info = await asyncio.to_thread(extract_youtube_info, song["title"] + " " + song["artist"])
            song["youtube_url"] = video_info["audio_url"]
            add_song(song)  # Update the database with the new youtube_url
            audio_url = video_info["audio_url"]
            logger.info(f"New Audio URL: {audio_url}")
        except Exception as inner_e:
            logger.error(f"Error finding a new youtube_url: {inner_e}")
            await channel.send("An error occurred while playing the song.")
            return

    guild_state.voice_client.play(
        FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS),
        after=lambda e: guild_state.skip_event.set(),
    )

    if song.get("from_playlist", False):
        embed, view = create_now_playing_from_playlist_embed(song, song["requester"], "❚❚")
    else:
        embed, view = create_now_playing_embed(song, song["requester"], "❚❚")

    guild_state.now_playing_message = await (
        song.get("message").edit(embed=embed, view=view)
        if song.get("message")
        else channel.send(embed=embed, view=view)
    )
    song["message"] = guild_state.now_playing_message

    await guild_state.skip_event.wait()
    await handle_song_finished(channel, guild_state, is_skipped=True)


async def handle_song_finished(
    channel: discord.TextChannel, guild_state: GuildMusicState, is_skipped: bool = False
) -> None:
    """
    Handles the cleanup after a song finishes playing and queues the next song.

    :param channel: The text channel where the now playing message was sent.
    :param guild_state: The current guild's music state.
    :param is_skipped: A boolean indicating whether the song was skipped.
    """
    logger.info(f"Song finished: {guild_state.current_song}")
    if guild_state.current_song:
        if guild_state.current_song.get("from_playlist", False):
            if is_skipped:
                embed = create_skipped_from_playlist_embed(guild_state.current_song, guild_state.current_song["requester"])
            else:
                embed = create_played_from_playlist_embed(guild_state.current_song, guild_state.current_song["requester"])
        else:
            if is_skipped:
                embed = create_skipped_embed(guild_state.current_song, guild_state.current_song["requester"])
            else:
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
        logger.info("Queue is empty, selecting the next song from the playlist.")
        next_song = guild_state.get_next_song()
        if next_song:
            next_song["message"] = None
            next_song["from_playlist"] = True  # Mark that this song is from the playlist
            await play_song(channel, next_song, guild_state)


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
        await handle_song_finished(interaction.channel, guild_state, is_skipped=True)
        return

    guild_state.add_skip_vote(user_id)

    skip_reaction = "⏭️"
    await guild_state.now_playing_message.add_reaction(skip_reaction)

    if len(guild_state.skip_votes) >= 2:
        guild_state.skip_event.set()
        await handle_song_finished(interaction.channel, guild_state, is_skipped=True)


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
            try:
                await guild_state.now_playing_message.edit(embed=embed, view=view)
            except discord.HTTPException as e:
                logger.error(f"Failed to edit message: {e}")
        return

    guild_state.add_pause_vote(user_id)

    pause_reaction = "⏸️"
    await guild_state.now_playing_message.add_reaction(pause_reaction)

    if len(guild_state.pause_votes) >= 2:
        try:
            if guild_state.voice_client.is_playing():
                guild_state.voice_client.pause()
                guild_state.is_paused = True
                embed, view = create_paused_embed(
                    guild_state.current_song,
                    guild_state.current_song["requester"],
                )
                await guild_state.now_playing_message.edit(embed=embed, view=view)
        except Exception as e:
            logger.error(f"Failed to pause playback on vote: {e}")
            await interaction.channel.send("An error occurred while processing pause vote.")
