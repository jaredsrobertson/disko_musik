import yt_dlp
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def extract_youtube_info(query: str) -> Optional[Dict[str, str]]:
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
        logger.error(f"Error extracting YouTube info: {e}")
        return None
