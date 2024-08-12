import logging
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Dict, Optional
from disk0muzik.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

logger = logging.getLogger(__name__)


class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=client_id, client_secret=client_secret
            )
        )

    def search_track(self, query: str) -> Optional[Dict[str, str]]:
        try:
            results = self.client.search(q=query, limit=1, type="track")
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


# Initialize the Spotify client
spotify_client = SpotifyClient(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)


def search_spotify(query: str) -> Optional[Dict[str, str]]:
    return spotify_client.search_track(query)
