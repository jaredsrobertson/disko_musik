import discord
import asyncio
import logging
from typing import Optional, Dict, List, Set
from disk0muzik.utils.database import get_all_songs
import random

logger = logging.getLogger(__name__)

class GuildMusicState:
    """
    Manages the state for a guild's music session, including the voice client,
    current queue, current song, vote tracking, and playlist management.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance of GuildMusicState, including loading and shuffling songs.
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

        self.played_songs: List[Dict[str, str]] = []
        self.unplayed_songs: List[Dict[str, str]] = self.load_and_shuffle_songs()

    def reset_state(self) -> None:
        """
        Resets the state of the music session, clearing the queue, current song, and votes.
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
        try:
            self.lock.release()
        except RuntimeError as e:
            logger.error(f"Lock release RuntimeError: {e}")

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
        if len(self.skip_votes) >= required_votes or user_id == self.current_song.get(
            "requester_id", -1
        ):
            self.skip_event.set()
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

    def load_and_shuffle_songs(self) -> List[Dict[str, str]]:
        """
        Loads all songs from the database and shuffles the order.

        Returns:
            List[Dict[str, str]]: A shuffled list of song dictionaries.
        """
        songs = get_all_songs()
        random.shuffle(songs)
        return songs

    def get_next_song(self) -> Optional[Dict[str, str]]:
        """
        Retrieves the next song to play, ensuring no repeats until all songs have been played.

        Returns:
            Optional[Dict[str, str]]: The next song to play, or None if no songs are available.
        """
        if not self.unplayed_songs:
            self.unplayed_songs = self.load_and_shuffle_songs()
            if (
                self.played_songs
                and self.unplayed_songs[0]["spotify_id"]
                == self.played_songs[-1]["spotify_id"]
            ):
                random.shuffle(self.unplayed_songs)

        if self.unplayed_songs:
            next_song = self.unplayed_songs.pop(0)
            self.played_songs.append(next_song)
            return next_song
        return None

    def reset_playlist(self) -> None:
        """
        Resets the playlist, allowing all songs to be played again in a new random order.
        """
        self.played_songs = []
        self.unplayed_songs = self.load_and_shuffle_songs()
