import pytest
from unittest.mock import patch, MagicMock
from disk0muzik.utils.database import (
    init_db,
    add_song,
    get_song,
    get_random_song,
    save_guild_state,
    load_guild_state,
    save_user_session,
    load_user_session,
)


@pytest.fixture
def sample_song():
    return {
        "spotify_id": "123",
        "title": "Test Song",
        "artist": "Test Artist",
        "youtube_url": "https://youtube.com/test",
        "requester": "test_user",
        "thumbnail": "https://image.url/test.jpg",
    }


@pytest.fixture
def sample_guild_state():
    return {
        "current_song": {"spotify_id": "123", "title": "Test Song"},
        "queue": [],
        "is_paused": False,
        "now_playing_message_id": 456789,
    }


@pytest.fixture
def sample_user_session():
    return {"session_key": "value"}


@patch("disk0muzik.utils.database.get_db_connection")
def test_init_db(mock_get_db_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    # Mock the context manager return value
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_db_connection.return_value = mock_conn

    init_db()

    assert mock_cursor.execute.call_count == 4
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()


def normalize_query(query):
    """Normalize SQL query by removing extra spaces and newlines."""
    return " ".join(query.split())


@patch("disk0muzik.utils.database.get_db_connection")
def test_add_song(mock_get_db_connection, sample_song):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    # Mock the context manager return value
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_db_connection.return_value = mock_conn

    add_song(sample_song)

    expected_query = """
        INSERT INTO songs (spotify_id, title, artist, thumbnail, youtube_url, requester)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (spotify_id) DO UPDATE 
        SET youtube_url = EXCLUDED.youtube_url, thumbnail = EXCLUDED.thumbnail
    """

    normalized_expected_query = normalize_query(expected_query)
    normalized_actual_query = normalize_query(mock_cursor.execute.call_args[0][0])

    assert normalized_actual_query == normalized_expected_query
    mock_cursor.execute.assert_called_once_with(
        mock_cursor.execute.call_args[0][
            0
        ],  # The actual query (already normalized above)
        (
            sample_song["spotify_id"],
            sample_song["title"],
            sample_song["artist"],
            sample_song["thumbnail"],  # Ensure the correct order
            sample_song["youtube_url"],
            sample_song["requester"],
        ),
    )
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()


@patch("disk0muzik.utils.database.get_db_connection")
def test_get_song(mock_get_db_connection, sample_song):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    # Mock the context manager return value
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (
        sample_song["spotify_id"],
        sample_song["title"],
        sample_song["artist"],
        sample_song["thumbnail"],
        sample_song["youtube_url"],
        sample_song["requester"],
    )
    mock_get_db_connection.return_value = mock_conn

    song = get_song("123")

    assert song == sample_song
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM songs WHERE spotify_id = %s", ("123",)
    )
    mock_conn.close.assert_called_once()


@patch("disk0muzik.utils.database.get_db_connection")
def test_get_random_song(mock_get_db_connection, sample_song):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    # Mock the context manager return value
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (
        sample_song["spotify_id"],
        sample_song["title"],
        sample_song["artist"],
        sample_song["thumbnail"],
        sample_song["youtube_url"],
        sample_song["requester"],
    )
    mock_get_db_connection.return_value = mock_conn

    song = get_random_song()

    assert song == sample_song
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM songs ORDER BY RANDOM() LIMIT 1"
    )
    mock_conn.close.assert_called_once()


@patch("disk0muzik.utils.database.get_db_connection")
def test_save_guild_state(mock_get_db_connection, sample_guild_state):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    # Mock the context manager return value
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_db_connection.return_value = mock_conn

    save_guild_state(1, sample_guild_state)

    expected_query = """
        INSERT INTO guild_states (guild_id, current_song, queue, is_paused, now_playing_message_id)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (guild_id) DO UPDATE 
        SET current_song = EXCLUDED.current_song,
            queue = EXCLUDED.queue,
            is_paused = EXCLUDED.is_paused,
            now_playing_message_id = EXCLUDED.now_playing_message_id
    """

    normalized_expected_query = normalize_query(expected_query)
    normalized_actual_query = normalize_query(mock_cursor.execute.call_args[0][0])

    assert normalized_actual_query == normalized_expected_query
    mock_cursor.execute.assert_called_once_with(
        mock_cursor.execute.call_args[0][
            0
        ],  # The actual query (already normalized above)
        (
            1,
            sample_guild_state["current_song"],
            sample_guild_state["queue"],
            sample_guild_state["is_paused"],
            sample_guild_state["now_playing_message_id"],
        ),
    )
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()


@patch("disk0muzik.utils.database.get_db_connection")
def test_load_guild_state(mock_get_db_connection, sample_guild_state):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    # Mock the context manager return value
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (
        1,
        sample_guild_state["current_song"],
        sample_guild_state["queue"],
        sample_guild_state["is_paused"],
        sample_guild_state["now_playing_message_id"],
    )
    mock_get_db_connection.return_value = mock_conn

    state = load_guild_state(1)

    assert state == {
        "guild_id": 1,
        "current_song": sample_guild_state["current_song"],
        "queue": sample_guild_state["queue"],
        "is_paused": sample_guild_state["is_paused"],
        "now_playing_message_id": sample_guild_state["now_playing_message_id"],
    }
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM guild_states WHERE guild_id = %s", (1,)
    )
    mock_conn.close.assert_called_once()


@patch("disk0muzik.utils.database.get_db_connection")
def test_save_user_session(mock_get_db_connection, sample_user_session):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    # Mock the context manager return value
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_db_connection.return_value = mock_conn

    save_user_session(1, sample_user_session)

    expected_query = """
        INSERT INTO user_sessions (user_id, session_data)
        VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE 
        SET session_data = EXCLUDED.session_data
    """

    normalized_expected_query = normalize_query(expected_query)
    normalized_actual_query = normalize_query(mock_cursor.execute.call_args[0][0])

    assert normalized_actual_query == normalized_expected_query
    mock_cursor.execute.assert_called_once_with(
        mock_cursor.execute.call_args[0][
            0
        ],  # The actual query (already normalized above)
        (1, sample_user_session),
    )
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()


@patch("disk0muzik.utils.database.get_db_connection")
def test_load_user_session(mock_get_db_connection, sample_user_session):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    # Mock the context manager return value
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (sample_user_session,)
    mock_get_db_connection.return_value = mock_conn

    session_data = load_user_session(1)

    assert session_data == sample_user_session
    mock_cursor.execute.assert_called_once_with(
        "SELECT session_data FROM user_sessions WHERE user_id = %s", (1,)
    )
    mock_conn.close.assert_called_once()
