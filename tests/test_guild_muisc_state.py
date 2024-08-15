import pytest
import asyncio
from disk0muzik.state.guild_music_state import GuildMusicState


def test_guild_music_state_initialization():
    guild_state = GuildMusicState()

    assert guild_state.voice_client is None
    assert guild_state.queue == []
    assert guild_state.current_song is None
    assert not guild_state.is_paused
    assert guild_state.now_playing_message is None
    assert isinstance(guild_state.skip_event, asyncio.Event)
    assert isinstance(guild_state.lock, asyncio.Lock)
