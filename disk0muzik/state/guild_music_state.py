import discord
import asyncio
from typing import Optional, Dict, List, Set


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

        # Initialize vote tracking as sets
        self.skip_votes: Set[int] = set()
        self.pause_votes: Set[int] = set()

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
        self.reset_votes()

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

    def add_skip_vote(self, user_id: int, required_votes: int) -> bool:
        """
        Adds a skip vote from the user. Returns True if the skip threshold is reached.

        Args:
            user_id (int): The ID of the user casting the vote.
            required_votes (int): The number of votes required to skip.

        Returns:
            bool: True if the skip threshold is reached, otherwise False.
        """
        self.skip_votes.add(user_id)
        print(required_votes)
        if len(self.skip_votes) >= required_votes or user_id == self.current_song.get(
            "requester_id"
        ):
            self.skip_event.set()  # Trigger the event to skip the song
            return True
        return False

    def add_pause_vote(self, user_id: int, required_votes: int) -> bool:
        """
        Adds a pause vote from the user. Returns True if the pause threshold is reached.

        Args:
            user_id (int): The ID of the user casting the vote.
            required_votes (int): The number of votes required to pause.

        Returns:
            bool: True if the pause threshold is reached, otherwise False.
        """
        self.pause_votes.add(user_id)
        print(required_votes)
        if len(self.pause_votes) >= required_votes or user_id == self.current_song.get(
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
