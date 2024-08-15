import psycopg2
from psycopg2 import OperationalError
from typing import Optional, Dict, Any
from disk0muzik.config import (
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
)

# SQL Queries as Constants
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

SELECT_RANDOM_SONG = "SELECT * FROM songs ORDER BY RANDOM() LIMIT 1"

SELECT_GUILD_STATE_BY_ID = "SELECT * FROM guild_states WHERE guild_id = %s"

SELECT_USER_SESSION_BY_ID = "SELECT session_data FROM user_sessions WHERE user_id = %s"


def get_db_connection():
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


def get_random_song() -> Optional[Dict[str, str]]:
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(SELECT_RANDOM_SONG)
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


def save_guild_state(guild_id: int, state: Dict[str, Any]):
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
