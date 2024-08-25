import discord
from discord.ui import Button, View
from typing import Tuple, Dict, Optional

BLANK_CHAR = "\u2003\u2800"

FOOTER_IMAGES = {
    "now_playing": "https://i.ibb.co/yP0591q/nowp5.gif",
    "paused": "https://i.ibb.co/2KtfHmw/pause-button.png",
    "queued": "https://i.ibb.co/m937VW1/add.png",
    "played": "https://i.ibb.co/9Wc3xNw/check.png",
}

EMBED_COLORS = {
    "now_playing": 0x1DB954,
    "paused": 0xFFA500,
    "queued": 0xFFFFFF,
    "played": 0x000000,
}


def create_embed(
    description: str,
    thumbnail_url: str,
    footer_text: str,
    footer_type: str,
) -> discord.Embed:
    """
    Creates a Discord embed with the specified parameters.

    :param description: The main content of the embed.
    :param thumbnail_url: URL of the thumbnail image.
    :param footer_text: Text to be displayed in the footer.
    :param footer_type: Type of the footer (now_playing, paused, queued, played).
    :return: The generated embed object.
    """
    embed = discord.Embed(description=description, color=EMBED_COLORS[footer_type])
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text=footer_text, icon_url=FOOTER_IMAGES[footer_type])
    return embed


def create_button(
    label: str, style: discord.ButtonStyle, custom_id: str, disabled: bool = False
) -> Button:
    """
    Creates a Discord button with the specified parameters.

    :param label: Text label for the button.
    :param style: Style of the button.
    :param custom_id: Custom ID to identify the button in callbacks.
    :param disabled: Whether the button is disabled or not.
    :return: The generated button object.
    """
    return Button(
        label=label,
        style=style,
        custom_id=custom_id,
        disabled=disabled,
    )


def create_description(song: Dict[str, str]) -> str:
    """
    Generates a formatted description for the embed using song details.

    :param song: Dictionary containing song details.
    :return: Formatted description string.
    """
    return f"# {song['title']}\n**{song['artist']}**\n\u2800\n{BLANK_CHAR * 17}"


def create_embed_and_view(
    song: Dict[str, str],
    requester: str,
    footer_type: str,
    play_pause_label: Optional[str] = None,
) -> Tuple[discord.Embed, Optional[View]]:
    """
    Generates an embed and view for different states like now playing, paused, queued, and played.

    :param song: Dictionary containing song details.
    :param requester: The user who requested the song.
    :param footer_type: Type of the footer (now_playing, paused, queued, played).
    :param play_pause_label: Label for the play/pause button.
    :return: The generated embed and view objects.
    """
    description = create_description(song)
    footer_text = f"{footer_type.replace('_', ' ').title()}\u2800•\u2800@{requester}"
    embed = create_embed(
        description,
        song.get("thumbnail", "default_thumbnail_url"),
        footer_text,
        footer_type,
    )

    view = None
    if footer_type in ["now_playing", "paused"]:
        view = View()
        view.add_item(
            create_button(
                play_pause_label or "❚❚",
                discord.ButtonStyle.primary,
                "play_pause_button",
            )
        )
        view.add_item(
            create_button(
                "▶▶",
                discord.ButtonStyle.primary,
                "skip_button",
            )
        )
    return embed, view


def create_now_playing_embed(
    song: Dict[str, str],
    requester: str,
    play_pause_label: str,
) -> Tuple[discord.Embed, View]:
    """
    Creates an embed for the 'Now Playing' state.

    :param song: Dictionary containing song details.
    :param requester: The user who requested the song.
    :param play_pause_label: Label for the play/pause button.
    :return: The generated embed and view objects.
    """
    return create_embed_and_view(song, requester, "now_playing", play_pause_label)


def create_paused_embed(
    song: Dict[str, str], requester: str
) -> Tuple[discord.Embed, View]:
    """
    Creates an embed for the 'Paused' state.

    :param song: Dictionary containing song details.
    :param requester: The user who requested the song.
    :return: The generated embed and view objects.
    """
    return create_embed_and_view(song, requester, "paused")


def create_queued_embed(
    song: Dict[str, str], requester: str
) -> Tuple[discord.Embed, View]:
    """
    Creates an embed for the 'Queued' state.

    :param song: Dictionary containing song details.
    :param requester: The user who requested the song.
    :return: The generated embed and view objects.
    """
    embed, _ = create_embed_and_view(song, requester, "queued")
    return embed, View()


def create_played_embed(song: Dict[str, str], requester: str) -> discord.Embed:
    """
    Creates an embed for the 'Played' state.

    :param song: Dictionary containing song details.
    :param requester: The user who requested the song.
    :return: The generated embed object.
    """
    embed, _ = create_embed_and_view(song, requester, "played")
    return embed
