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


def search_spotify(query: str) -> Optional[Dict[str, str]]:
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
        logger.error(f"Spotify search error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    return None
