import psycopg2
from psycopg2 import OperationalError
from typing import Optional, Dict
from disk0muzik.config import (
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
)


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
        print(f"Error connecting to the database: {e}")
        return None


def init_db():
    conn = get_db_connection()
    if conn:
        try:
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
        finally:
            conn.close()


def add_song(song: Dict[str, str]):
    conn = get_db_connection()
    if conn:
        try:
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
        finally:
            conn.close()


def get_song(spotify_id: str) -> Optional[Dict[str, str]]:
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM songs WHERE spotify_id = %s", (spotify_id,))
                row = cur.fetchone()
                if row:
                    return {
                        "spotify_id": row[0],
                        "title": row[1],
                        "artist": row[2],
                        "youtube_url": row[3],
                        "requester": row[4],
                        "thumbnail": row[5],
                    }
        finally:
            conn.close()
    return None


def get_random_song() -> Optional[Dict[str, str]]:
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM songs ORDER BY RANDOM() LIMIT 1")
                row = cur.fetchone()
                if row:
                    return {
                        "spotify_id": row[0],
                        "title": row[1],
                        "artist": row[2],
                        "youtube_url": row[3],
                        "requester": row[4],
                        "thumbnail": row[5],
                    }
        finally:
            conn.close()
    return None
