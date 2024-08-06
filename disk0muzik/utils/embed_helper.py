import discord
from discord.ui import Button, View
from typing import Tuple, Dict

BLANK_CHAR = "\u2003\u2800"

# Footer images
NOW_PLAYING_FOOTER_IMAGE = "https://i.ibb.co/yP0591q/nowp5.gif"
PAUSED_FOOTER_IMAGE = "https://i.ibb.co/2KtfHmw/pause-button.png"
QUEUED_FOOTER_IMAGE = "https://i.ibb.co/m937VW1/add.png"
PLAYED_FOOTER_IMAGE = "https://i.ibb.co/9Wc3xNw/check.png"

# Embed colors
COLOR_NOW_PLAYING = 0x1DB954  # Green
COLOR_PAUSED = 0xFFA500  # Rich orange
COLOR_QUEUED = 0xFFFFFF  # White
COLOR_PLAYED = 0x000000  # Black


def create_embed(
    description: str,
    thumbnail_url: str,
    footer_text: str,
    footer_icon_url: str,
    color: int,
) -> discord.Embed:
    embed = discord.Embed(description=description, color=color)
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text=footer_text, icon_url=footer_icon_url)
    return embed


def create_button(
    label: str, style: discord.ButtonStyle, custom_id: str, disabled: bool = False
) -> Button:
    return Button(
        label=label,
        style=style,
        custom_id=custom_id,
        disabled=disabled,
    )


def create_description(song: Dict[str, str]) -> str:
    return f"# {song['title']}\n**{song['artist']}**\n\u2800\n{BLANK_CHAR * 17}"


def create_now_playing_embed(
    song: Dict[str, str], requester: str, play_pause_label: str
) -> Tuple[discord.Embed, View]:
    description = create_description(song)
    footer_text = f"Now Playing\u2800•\u2800@{requester}"
    embed = create_embed(
        description,
        song.get("thumbnail", "default_thumbnail_url"),
        footer_text,
        NOW_PLAYING_FOOTER_IMAGE,
        color=COLOR_NOW_PLAYING,
    )

    view = View()
    view.add_item(
        create_button(
            play_pause_label, discord.ButtonStyle.primary, "play_pause_button"
        )
    )
    view.add_item(create_button("▶▶", discord.ButtonStyle.primary, "skip_button"))
    view.add_item(
        create_button(
            f"{BLANK_CHAR * 15}\u2800",
            discord.ButtonStyle.secondary,
            "placeholder",
            True,
        )
    )
    return embed, view


def create_paused_embed(
    song: Dict[str, str], requester: str
) -> Tuple[discord.Embed, View]:
    description = create_description(song)
    footer_text = f"Paused\u2800•\u2800@{requester}"
    embed = create_embed(
        description,
        song.get("thumbnail", "default_thumbnail_url"),
        footer_text,
        PAUSED_FOOTER_IMAGE,
        color=COLOR_PAUSED,
    )

    view = View()
    view.add_item(create_button("▶", discord.ButtonStyle.primary, "play_pause_button"))
    view.add_item(create_button("▶▶", discord.ButtonStyle.primary, "skip_button"))
    view.add_item(
        create_button(
            f"{BLANK_CHAR * 15}\u2800",
            discord.ButtonStyle.secondary,
            "placeholder",
            True,
        )
    )
    return embed, view


def create_queued_embed(
    song: Dict[str, str], requester: str
) -> Tuple[discord.Embed, View]:
    description = create_description(song)
    footer_text = f"Queued\u2800•\u2800@{requester}"
    embed = create_embed(
        description,
        song.get("thumbnail", "default_thumbnail_url"),
        footer_text,
        QUEUED_FOOTER_IMAGE,
        color=COLOR_QUEUED,
    )

    view = View()
    return embed, view


def create_played_embed(song: Dict[str, str], requester: str) -> discord.Embed:
    description = create_description(song)
    footer_text = f"Played\u2800•\u2800@{requester}"
    return create_embed(
        description,
        song.get("thumbnail", "default_thumbnail_url"),
        footer_text,
        PLAYED_FOOTER_IMAGE,
        color=COLOR_PLAYED,
    )
