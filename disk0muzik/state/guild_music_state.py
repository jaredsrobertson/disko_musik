import discord
import asyncio
from typing import Optional, Dict, List, Set


class GuildMusicState:
    """
    Manages the state for a guild's music session, including the voice client,
    current queue, current song, and related state information.
    """

    def __init__(self) -> None:
        """
        Initializes the GuildMusicState, setting up the voice client, queue,
        current song, and vote tracking mechanisms.
        """
        self.voice_client: Optional[discord.VoiceClient] = None
        self.queue: List[Dict[str, str]] = []
        self.current_song: Optional[Dict[str, str]] = None
        self.is_paused: bool = False
        self.now_playing_message: Optional[discord.Message] = None
        self.skip_event = asyncio.Event()
        self.lock = asyncio.Lock()
        self.skip_votes: Set[int] = set()
        self.pause_votes: Set[int] = set()

    def reset_state(self) -> None:
        """
        Resets the state of the music session, clearing the queue, current song,
        and vote counts. Also clears the skip event.
        """
        self.queue.clear()
        self.current_song = None
        self.is_paused = False
        self.now_playing_message = None
        self.skip_event.clear()
        self.reset_votes()

    async def __aenter__(self) -> None:
        """
        Acquires the lock asynchronously when entering a context.
        """
        await self.lock.acquire()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Releases the lock when exiting a context.
        """
        self.lock.release()

    def add_skip_vote(self, user_id: int) -> bool:
        """
        Adds a skip vote from the user. Returns True if the skip threshold is reached.

        :param user_id: The ID of the user casting the skip vote.
        :return: True if the song should be skipped, False otherwise.
        """
        self.skip_votes.add(user_id)
        if len(self.skip_votes) >= 2 or user_id == self.current_song.get(
            "requester_id"
        ):
            self.skip_event.set()
            return True
        return False

    def add_pause_vote(self, user_id: int) -> bool:
        """
        Adds a pause vote from the user. Returns True if the pause threshold is reached.

        :param user_id: The ID of the user casting the pause vote.
        :return: True if the song should be paused, False otherwise.
        """
        self.pause_votes.add(user_id)
        if len(self.pause_votes) >= 2 or user_id == self.current_song.get(
            "requester_id"
        ):
            return True
        return False

    def reset_votes(self) -> None:
        """
        Resets the skip and pause votes.
        """
        self.skip_votes.clear()
        self.pause_votes.clear()
