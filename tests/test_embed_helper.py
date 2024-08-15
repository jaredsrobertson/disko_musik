import pytest
import discord
from disk0muzik.utils.embed_helper import (
    create_embed_and_view,
    FOOTER_IMAGES,
    EMBED_COLORS,
)


@pytest.fixture
def sample_song():
    return {
        "spotify_id": "123",
        "title": "Test Song",
        "artist": "Test Artist",
        "thumbnail": "https://image.url/test.jpg",
        "youtube_url": "https://youtube.com/test",
        "requester": "test_user",
    }


@pytest.mark.asyncio
async def test_create_embed_and_view(sample_song):
    footer_type = "now_playing"
    embed, view = create_embed_and_view(
        sample_song, sample_song["requester"], footer_type, "❚❚"
    )

    assert isinstance(embed, discord.Embed)
    assert (
        embed.description
        == f"# Test Song\n**Test Artist**\n\u2800\n{'\u2003\u2800' * 17}"
    )
    assert embed.color.value == EMBED_COLORS[footer_type]  # Compare the value
    assert embed.footer.icon_url == FOOTER_IMAGES[footer_type]

    assert isinstance(view, discord.ui.View)
    assert len(view.children) > 0
