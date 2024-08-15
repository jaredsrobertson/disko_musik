import logging
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Dict, Optional
from disk0muzik.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

logger = logging.getLogger(__name__)

# Initialize Spotify client
sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET
    )
)


def log_error(context: str, error: Exception, query: str) -> None:
    """
    Logs an error with context and query information.

    Args:
        context (str): Description of the context where the error occurred.
        error (Exception): The exception that was raised.
        query (str): The query that caused the error.
    """
    logger.error(f"{context} - Query: '{query}' - Error: {error}")


def search_spotify(query: str) -> Optional[Dict[str, str]]:
    """
    Searches Spotify for a track matching the query.

    Args:
        query (str): The search query to find the track on Spotify.

    Returns:
        Optional[Dict[str, str]]: A dictionary with track details or None if no track is found.
    """
    try:
        results = sp.search(q=query, limit=1, type="track")
        if results["tracks"]["items"]:
            track = results["tracks"]["items"][0]
            return {
                "title": track["name"],
                "artist": track["artists"][0]["name"],
                "album_art": track["album"]["images"][0]["url"],
                "spotify_id": track["id"],
            }
    except spotipy.exceptions.SpotifyException as e:
        log_error("Spotify search error", e, query)
    except Exception as e:
        log_error("Unexpected error during Spotify search", e, query)
    return None
