import logging
from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool
from psycopg2 import OperationalError
from typing import Optional, Dict
from disk0muzik.config import (
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize connection pool (example values; adjust accordingly)
pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dbname=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
)


@contextmanager
def get_db_connection():
    conn = pool.getconn()
    try:
        yield conn
    except OperationalError as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        pool.putconn(conn)


def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """CREATE TABLE IF NOT EXISTS songs (
                     spotify_id TEXT PRIMARY KEY,
                     title TEXT,
                     artist TEXT,
                     youtube_url TEXT,
                     requester TEXT,
                     thumbnail TEXT
                   )"""
            )
            conn.commit()


def add_song(song: Dict[str, str]):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO songs (spotify_id, title, artist, youtube_url, requester, thumbnail)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   ON CONFLICT (spotify_id) DO UPDATE 
                   SET youtube_url = EXCLUDED.youtube_url, thumbnail = EXCLUDED.thumbnail""",
                (
                    song["spotify_id"],
                    song["title"],
                    song["artist"],
                    song["youtube_url"],
                    song["requester"],
                    song["thumbnail"],
                ),
            )
            conn.commit()


def get_song(spotify_id: str) -> Optional[Dict[str, str]]:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM songs WHERE spotify_id = %s", (spotify_id,))
            row = cur.fetchone()
            if row:
                return {
                    "spotify_id": row[0],
                    "title": row[1],
                    "artist": row[2],
                    "thumbnail": row[3],
                    "youtube_url": row[4],
                    "requester": row[5],
                }
    return None


def get_random_song() -> Optional[Dict[str, str]]:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM songs ORDER BY RANDOM() LIMIT 1")
            row = cur.fetchone()
            if row:
                return {
                    "spotify_id": row[0],
                    "title": row[1],
                    "artist": row[2],
                    "thumbnail": row[3],
                    "youtube_url": row[4],
                    "requester": row[5],
                }
    return None
