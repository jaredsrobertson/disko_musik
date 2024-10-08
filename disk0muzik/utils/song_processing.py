import logging
import asyncio
from typing import Optional, Dict
from disk0muzik.utils.spotify_helper import search_spotify
from disk0muzik.utils.yt_dlp_helper import extract_youtube_info
from disk0muzik.utils.database import get_song, add_song

logger = logging.getLogger(__name__)

async def process_song_query(
    query: str, requester: str, requester_id: int
) -> Optional[Dict[str, str]]:
    """
    Processes a song query by searching Spotify and YouTube, and returns song details.
 
    Parameters:
        query (str): The query string to search for the song.
        requester (str): The name of the user requesting the song.
        requester_id (int): The ID of the user requesting the song.
 
    Returns:
        Optional[Dict[str, str]]: A dictionary containing song details or None if the song could not be found.
    """
    try:
        if "youtube.com" in query or "youtu.be" in query:
            logger.info(f"Processing YouTube URL: {query}")
            video_info = await asyncio.to_thread(extract_youtube_info, query)
            if not video_info:
                logger.error("Couldn't extract video info from YouTube URL.")
                return None

            spotify_result = await asyncio.to_thread(search_spotify, video_info["title"])
            if not spotify_result:
                logger.error("Couldn't find the song on Spotify.")
                return None

            existing_song = get_song(spotify_result["spotify_id"])
            if existing_song:
                logger.info(f"Using existing YouTube URL from the database: {existing_song['youtube_url']}")
                youtube_url = existing_song["youtube_url"]
            else:
                youtube_url = video_info["video_url"]

            song = {
                "spotify_id": spotify_result["spotify_id"],
                "title": spotify_result["title"],
                "artist": spotify_result["artist"],
                "thumbnail": spotify_result["album_art"],
                "youtube_url": youtube_url,
                "requester": requester,
                "requester_id": requester_id,
            }

            add_song(song)

        else:
            logger.info(f"Searching Spotify for query: {query}")
            spotify_result = await asyncio.to_thread(search_spotify, query)
            if not spotify_result:
                logger.error("Couldn't find the song on Spotify.")
                return None

            existing_song = get_song(spotify_result["spotify_id"])
            if existing_song:
                logger.info(f"Using existing YouTube URL from the database: {existing_song['youtube_url']}")
                youtube_url = existing_song["youtube_url"]
            else:
                youtube_info = await asyncio.to_thread(
                    extract_youtube_info,
                    f"{spotify_result['artist']} {spotify_result['title']}",
                )
                if not youtube_info:
                    logger.error("Couldn't find the song on YouTube.")
                    return None
                youtube_url = youtube_info["video_url"]

            song = {
                "spotify_id": spotify_result["spotify_id"],
                "title": spotify_result["title"],
                "artist": spotify_result["artist"],
                "thumbnail": spotify_result["album_art"],
                "youtube_url": youtube_url,
                "requester": requester,
                "requester_id": requester_id,
            }

            add_song(song)

        return song

    except Exception as e:
        logger.error(f"Error processing song query: {e}")
        return None
