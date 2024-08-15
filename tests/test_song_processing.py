import pytest
from unittest.mock import patch
from disk0muzik.utils.song_processing import process_song_query


@pytest.mark.asyncio
@patch("disk0muzik.utils.song_processing.search_spotify")
@patch("disk0muzik.utils.song_processing.extract_youtube_info")
async def test_process_song_query(mock_extract_youtube_info, mock_search_spotify):
    mock_search_spotify.return_value = {
        "spotify_id": "123",
        "title": "Test Song",
        "artist": "Test Artist",
        "album_art": "https://image.url/test.jpg",
    }
    mock_extract_youtube_info.return_value = {
        "video_url": "https://youtube.com/video-url",
        "audio_url": "https://youtube.com/audio-url",
        "title": "Test Video",
        "thumbnail": "https://youtube.com/thumbnail.jpg",
    }

    result = await process_song_query("Test Query", "test_user")

    assert result["spotify_id"] == "123"
    assert result["title"] == "Test Song"
    assert result["artist"] == "Test Artist"
