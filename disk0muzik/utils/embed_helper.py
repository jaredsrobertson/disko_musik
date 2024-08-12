import discord
from discord.ui import Button, View
from typing import Tuple, Dict

# Constants
BLANK_CHAR = "\u2003\u2800"
DEFAULT_THUMBNAIL_URL = "https://example.com/default_thumbnail.png"

# Footer images
FOOTER_IMAGES = {
    "now_playing": "https://i.ibb.co/yP0591q/nowp5.gif",
    "paused": "https://i.ibb.co/2KtfHmw/pause-button.png",
    "queued": "https://i.ibb.co/m937VW1/add.png",
    "played": "https://i.ibb.co/9Wc3xNw/check.png",
}

# Embed colors
EMBED_COLORS = {
    "now_playing": 0x1DB954,  # Green
    "paused": 0xFFA500,  # Rich orange
    "queued": 0xFFFFFF,  # White
    "played": 0x000000,  # Black
}


def create_embed(
    description: str, thumbnail_url: str, footer_text: str, footer_type: str
) -> discord.Embed:
    embed = discord.Embed(description=description, color=EMBED_COLORS[footer_type])
    embed.set_thumbnail(url=thumbnail_url or DEFAULT_THUMBNAIL_URL)
    embed.set_footer(text=footer_text, icon_url=FOOTER_IMAGES[footer_type])
    return embed


def create_button(
    label: str, style: discord.ButtonStyle, custom_id: str, disabled: bool = False
) -> Button:
    return Button(label=label, style=style, custom_id=custom_id, disabled=disabled)


def create_description(song: Dict[str, str]) -> str:
    return f"# {song['title']}\n**{song['artist']}**\n\u2800\n{BLANK_CHAR * 17}"


def create_now_playing_embed(
    song: Dict[str, str], requester: str, play_pause_label: str
) -> Tuple[discord.Embed, View]:
    description = create_description(song)
    footer_text = f"Now Playing\u2800•\u2800@{requester}"
    embed = create_embed(description, song.get("thumbnail"), footer_text, "now_playing")

    view = View()
    view.add_item(
        create_button(
            play_pause_label, discord.ButtonStyle.primary, "play_pause_button"
        )
    )
    view.add_item(create_button("▶▶", discord.ButtonStyle.primary, "skip_button"))
    return embed, view


def create_paused_embed(
    song: Dict[str, str], requester: str
) -> Tuple[discord.Embed, View]:
    description = create_description(song)
    footer_text = f"Paused\u2800•\u2800@{requester}"
    embed = create_embed(description, song.get("thumbnail"), footer_text, "paused")

    view = View()
    view.add_item(create_button("▶", discord.ButtonStyle.primary, "play_pause_button"))
    view.add_item(create_button("▶▶", discord.ButtonStyle.primary, "skip_button"))
    return embed, view


def create_queued_embed(
    song: Dict[str, str], requester: str
) -> Tuple[discord.Embed, View]:
    description = create_description(song)
    footer_text = f"Queued\u2800•\u2800@{requester}"
    embed = create_embed(description, song.get("thumbnail"), footer_text, "queued")

    view = View()
    return embed, view


def create_played_embed(song: Dict[str, str], requester: str) -> discord.Embed:
    description = create_description(song)
    footer_text = f"Played\u2800•\u2800@{requester}"
    return create_embed(description, song.get("thumbnail"), footer_text, "played")
