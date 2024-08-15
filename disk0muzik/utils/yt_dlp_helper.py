import yt_dlp
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def log_error(context: str, error: Exception, query: str) -> None:
    """
    Logs an error with context and query information.

    Args:
        context (str): Description of the context where the error occurred.
        error (Exception): The exception that was raised.
        query (str): The query that caused the error.
    """
    logger.error(f"{context} - Query: '{query}' - Error: {error}")


def extract_youtube_info(query: str) -> Optional[Dict[str, str]]:
    """
    Extracts video and audio information from YouTube for a given query.

    Args:
        query (str): The search query or YouTube URL.

    Returns:
        Optional[Dict[str, str]]: A dictionary with video and audio details or None if extraction fails.
    """
    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "skip_download": True,
        "default_search": "ytsearch1",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(query, download=False)
            if "entries" in info_dict:
                info_dict = info_dict["entries"][0]
            return {
                "video_url": f"https://www.youtube.com/watch?v={info_dict['id']}",
                "audio_url": info_dict["url"],
                "thumbnail": info_dict.get("thumbnail"),
                "title": info_dict.get("title"),
            }
    except yt_dlp.DownloadError as e:
        log_error("Error extracting YouTube info", e, query)
    except Exception as e:
        log_error("Unexpected error during YouTube info extraction", e, query)
    return None
