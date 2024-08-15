import discord
import asyncio
from typing import Optional, Dict, List


class GuildMusicState:
    """
    Manages the state for a guild's music session, including the voice client,
    current queue, current song, and related state information.
    """

    def __init__(self) -> None:
        self.voice_client: Optional[discord.VoiceClient] = None
        self.queue: List[Dict[str, str]] = []
        self.current_song: Optional[Dict[str, str]] = None
        self.is_paused: bool = False
        self.now_playing_message: Optional[discord.Message] = None
        self.skip_event = asyncio.Event()
        self.lock = asyncio.Lock()

    def reset_state(self) -> None:
        """
        Resets the state of the music session, clearing the queue and current song.
        This is useful when the bot leaves the voice channel or needs to reset its state.
        """
        self.queue.clear()
        self.current_song = None
        self.is_paused = False
        self.now_playing_message = None
        self.skip_event.clear()

    async def __aenter__(self):
        """
        Asynchronous context manager entry to acquire the lock.
        """
        await self.lock.acquire()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Asynchronous context manager exit to release the lock.
        """
        self.lock.release()
