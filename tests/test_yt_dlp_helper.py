import pytest
from unittest.mock import patch
from disk0muzik.utils.yt_dlp_helper import extract_youtube_info


@patch("disk0muzik.utils.yt_dlp_helper.yt_dlp.YoutubeDL.extract_info")
def test_extract_youtube_info(mock_extract_info):
    mock_extract_info.return_value = {
        "id": "abcd1234",
        "url": "https://youtube.com/audio-url",
        "thumbnail": "https://youtube.com/thumbnail.jpg",
        "title": "Test Video",
    }

    result = extract_youtube_info("Test Query")

    assert result["video_url"] == "https://www.youtube.com/watch?v=abcd1234"
    assert result["audio_url"] == "https://youtube.com/audio-url"
    assert result["thumbnail"] == "https://youtube.com/thumbnail.jpg"
    assert result["title"] == "Test Video"


@patch("disk0muzik.utils.yt_dlp_helper.yt_dlp.YoutubeDL.extract_info")
def test_extract_youtube_info_no_results(mock_extract_info):
    mock_extract_info.side_effect = Exception("Error extracting info")

    result = extract_youtube_info("Invalid Query")

    assert result is None
