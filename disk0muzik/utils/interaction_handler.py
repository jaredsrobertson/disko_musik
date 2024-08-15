import logging
import discord
from disk0muzik.utils.embed_helper import create_now_playing_embed, create_paused_embed

logger = logging.getLogger(__name__)


async def handle_button_click(
    interaction: discord.Interaction, get_guild_state
) -> None:
    guild_id = interaction.guild_id
    guild_state = get_guild_state(guild_id)

    button_id = interaction.data.get("custom_id")
    logger.info(f"Button clicked: {button_id}")
    if guild_state.current_song and button_id == "play_pause_button":
        if guild_state.voice_client.is_playing():
            guild_state.voice_client.pause()
            guild_state.is_paused = True
            embed, view = create_paused_embed(
                guild_state.current_song, guild_state.current_song["requester"]
            )
            await guild_state.now_playing_message.edit(embed=embed, view=view)
            logger.info("Paused song.")
        elif guild_state.is_paused:
            guild_state.voice_client.resume()
            guild_state.is_paused = False
            embed, view = create_now_playing_embed(
                guild_state.current_song,
                guild_state.current_song["requester"],
                "❚❚",
            )
            await guild_state.now_playing_message.edit(embed=embed, view=view)
            logger.info("Resumed song.")
    elif guild_state.current_song and button_id == "skip_button":
        if guild_state.voice_client.is_playing() or guild_state.is_paused:
            guild_state.voice_client.stop()
            guild_state.is_paused = False
            guild_state.skip_event.set()
            logger.info("Skipped song.")


async def on_interaction(interaction: discord.Interaction, get_guild_state) -> None:
    logger.info(f"Interaction received: {interaction.data.get('custom_id')}")
    if interaction.type == discord.InteractionType.component:
        await interaction.response.defer()
        await handle_button_click(interaction, get_guild_state)
