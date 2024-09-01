import psycopg2
from psycopg2 import OperationalError
from typing import Optional, Dict, Any, List
import asyncio
from disk0muzik.config import (
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
)
import random

CREATE_SONGS_TABLE = """
CREATE TABLE IF NOT EXISTS songs (
    spotify_id TEXT PRIMARY KEY,
    title TEXT,
    artist TEXT,
    thumbnail TEXT,
    youtube_url TEXT,
    requester TEXT   
)
"""

CREATE_SPOTIFY_ID_INDEX = (
    "CREATE INDEX IF NOT EXISTS idx_spotify_id ON songs (spotify_id)"
)

CREATE_GUILD_STATES_TABLE = """
CREATE TABLE IF NOT EXISTS guild_states (
    guild_id BIGINT PRIMARY KEY,
    current_song JSONB,
    queue JSONB,
    is_paused BOOLEAN,
    now_playing_message_id BIGINT
)
"""

CREATE_USER_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS user_sessions (
    user_id BIGINT PRIMARY KEY,
    session_data JSONB
)
"""

INSERT_OR_UPDATE_SONG = """
INSERT INTO songs (spotify_id, title, artist, thumbnail, youtube_url, requester)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (spotify_id) DO UPDATE 
SET youtube_url = EXCLUDED.youtube_url, thumbnail = EXCLUDED.thumbnail
"""

INSERT_OR_UPDATE_GUILD_STATE = """
INSERT INTO guild_states (guild_id, current_song, queue, is_paused, now_playing_message_id)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (guild_id) DO UPDATE 
SET current_song = EXCLUDED.current_song,
    queue = EXCLUDED.queue,
    is_paused = EXCLUDED.is_paused,
    now_playing_message_id = EXCLUDED.now_playing_message_id
"""

INSERT_OR_UPDATE_USER_SESSION = """
INSERT INTO user_sessions (user_id, session_data)
VALUES (%s, %s)
ON CONFLICT (user_id) DO UPDATE 
SET session_data = EXCLUDED.session_data
"""

SELECT_SONG_BY_SPOTIFY_ID = "SELECT * FROM songs WHERE spotify_id = %s"

SELECT_ALL_SONGS = "SELECT * FROM songs"

SELECT_GUILD_STATE_BY_ID = "SELECT * FROM guild_states WHERE guild_id = %s"

SELECT_USER_SESSION_BY_ID = "SELECT session_data FROM user_sessions WHERE user_id = %s"


def get_db_connection():
    """
    Establishes and returns a connection to the PostgreSQL database.

    Returns:
        psycopg2.connection: A connection object to the database.
    
    Raises:
        RuntimeError: If the connection to the database fails.
    """
    try:
        conn = psycopg2.connect(
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
        )
        return conn
    except OperationalError as e:
        raise RuntimeError(f"Error connecting to the database: {e}")


def init_db():
    """
    Initializes the database by creating the necessary tables and indexes if they do not already exist.
    """
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(CREATE_SONGS_TABLE)
                cur.execute(CREATE_SPOTIFY_ID_INDEX)
                cur.execute(CREATE_GUILD_STATES_TABLE)
                cur.execute(CREATE_USER_SESSIONS_TABLE)
                conn.commit()
        finally:
            conn.close()


def add_song(song: Dict[str, str]):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                existing_song = get_song(song["spotify_id"])
                
                # Insert a new song entry if it doesn't exist
                # or update if youtube_url is missing or broken
                if not existing_song or not existing_song["youtube_url"]:
                    cur.execute(
                        INSERT_OR_UPDATE_SONG,
                        (
                            song["spotify_id"],
                            song["title"],
                            song["artist"],
                            song["thumbnail"],
                            song["youtube_url"],
                            song["requester"],
                        ),
                    )
                conn.commit()
        finally:
            conn.close()


def get_song(spotify_id: str) -> Optional[Dict[str, str]]:
    """
    Retrieves a song from the database by its Spotify ID.

    Args:
        spotify_id (str): The Spotify ID of the song.

    Returns:
        Optional[Dict[str, str]]: A dictionary containing the song details if found, else None.
    """
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(SELECT_SONG_BY_SPOTIFY_ID, (spotify_id,))
                row = cur.fetchone()
                if row:
                    return {
                        "spotify_id": row[0],
                        "title": row[1],
                        "artist": row[2],
                        "youtube_url": row[4],
                        "requester": row[5],
                        "thumbnail": row[3],
                    }
        finally:
            conn.close()
    return None


def get_all_songs() -> List[Dict[str, str]]:
    """
    Retrieves all songs from the database.

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing song details.
    """
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(SELECT_ALL_SONGS)
                rows = cur.fetchall()
                return [
                    {
                        "spotify_id": row[0],
                        "title": row[1],
                        "artist": row[2],
                        "youtube_url": row[4],
                        "requester": row[5],
                        "thumbnail": row[3],
                    }
                    for row in rows
                ]
        finally:
            conn.close()
    return []


class GuildMusicState:
    """
    Manages the state for a guild's music session, including the voice client,
    current queue, current song, and related state information.
    """

    def __init__(self):
        """
        Initializes a new instance of GuildMusicState, including loading and shuffling songs.
        """
        self.voice_client = None
        self.queue = []
        self.current_song = None
        self.is_paused = False
        self.now_playing_message = None
        self.skip_event = asyncio.Event()
        self.lock = asyncio.Lock()
        self.played_songs = []
        self.unplayed_songs = self.load_and_shuffle_songs()

    def load_and_shuffle_songs(self) -> List[Dict[str, str]]:
        """
        Loads all songs from the database, shuffles the order, and ensures that the first song 
        in the shuffled playlist is not the same as the last played song.

        Returns:
            List[Dict[str, str]]: A shuffled list of song dictionaries.
        """
        songs = get_all_songs()
        if not songs:
            return []

        last_song = self.played_songs[-1] if self.played_songs else None

        # Remove the last played song from the list before shuffling
        if last_song:
            songs.remove(last_song)

        # Shuffle the songs
        random.shuffle(songs)

        # Insert the last played song back into the playlist at a random position that is not the start
        if last_song:
            insert_position = random.randint(1, len(songs))
            songs.insert(insert_position, last_song)

        return songs

    def get_next_song(self) -> Optional[Dict[str, str]]:
        """
        Retrieves the next song to play, ensuring no repeats until all songs have been played.

        Returns:
            Optional[Dict[str, str]]: The next song to play, or None if no songs are available.
        """
        if not self.unplayed_songs:
            self.unplayed_songs = self.load_and_shuffle_songs()

        if self.unplayed_songs:
            next_song = self.unplayed_songs.pop(0)
            self.played_songs.append(next_song)
            return next_song
        return None

    def reset_playlist(self):
        """
        Resets the playlist, allowing all songs to be played again in a new random order.
        """
        self.played_songs = []
        self.unplayed_songs = self.load_and_shuffle_songs()


def save_guild_state(guild_id: int, state: Dict[str, Any]):
    """
    Saves the current state of a guild's music session to the database.

    Args:
        guild_id (int): The ID of the guild.
        state (Dict[str, Any]): The current state of the guild's music session.
    """
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    INSERT_OR_UPDATE_GUILD_STATE,
                    (
                        guild_id,
                        state["current_song"],
                        state["queue"],
                        state["is_paused"],
                        state["now_playing_message_id"],
                    ),
                )
                conn.commit()
        finally:
            conn.close()


def load_guild_state(guild_id: int) -> Optional[Dict[str, Any]]:
    """
    Loads the saved state of a guild's music session from the database.

    Args:
        guild_id (int): The ID of the guild.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing the state of the guild's music session if found, else None.
    """
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(SELECT_GUILD_STATE_BY_ID, (guild_id,))
                row = cur.fetchone()
                if row:
                    return {
                        "guild_id": row[0],
                        "current_song": row[1],
                        "queue": row[2],
                        "is_paused": row[3],
                        "now_playing_message_id": row[4],
                    }
        finally:
            conn.close()
    return None


def save_user_session(user_id: int, session_data: Dict[str, Any]):
    """
    Saves a user's session data to the database.

    Args:
        user_id (int): The ID of the user.
        session_data (Dict[str, Any]): The session data to save.
    """
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    INSERT_OR_UPDATE_USER_SESSION,
                    (
                        user_id,
                        session_data,
                    ),
                )
                conn.commit()
        finally:
            conn.close()


def load_user_session(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Loads a user's session data from the database.

    Args:
        user_id (int): The ID of the user.

    Returns:
        Optional[Dict[str, Any]]: The session data if found, else None.
    """
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(SELECT_USER_SESSION_BY_ID, (user_id,))
                row = cur.fetchone()
                if row:
                    return row[0]
        finally:
            conn.close()
    return None
