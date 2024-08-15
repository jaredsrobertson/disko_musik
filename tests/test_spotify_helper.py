import pytest
from unittest.mock import patch
from disk0muzik.utils.spotify_helper import search_spotify


@patch("disk0muzik.utils.spotify_helper.sp.search")
def test_search_spotify(mock_spotify_search):
    mock_spotify_search.return_value = {
        "tracks": {
            "items": [
                {
                    "name": "Test Song",
                    "artists": [{"name": "Test Artist"}],
                    "album": {"images": [{"url": "https://image.url/test.jpg"}]},
                    "id": "123",
                }
            ]
        }
    }

    result = search_spotify("Test Song")

    assert result["title"] == "Test Song"
    assert result["artist"] == "Test Artist"
    assert result["album_art"] == "https://image.url/test.jpg"
    assert result["spotify_id"] == "123"


@patch("disk0muzik.utils.spotify_helper.sp.search")
def test_search_spotify_no_results(mock_spotify_search):
    mock_spotify_search.return_value = {"tracks": {"items": []}}

    result = search_spotify("Non-existent Song")

    assert result is None
