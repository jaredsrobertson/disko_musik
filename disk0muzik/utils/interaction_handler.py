import logging
import discord
from disk0muzik.utils.embed_helper import create_now_playing_embed, create_paused_embed

logger = logging.getLogger(__name__)

SKIP_EMOJI = "⏩"
PAUSE_EMOJI = "⏸️"


async def handle_button_click(
    interaction: discord.Interaction, get_guild_state
) -> None:
    """
    Handles button click interactions for skip and pause buttons.

    Args:
        interaction (discord.Interaction): The interaction triggered by the button click.
        get_guild_state (function): A function that retrieves the guild's music state.
    """
    guild_id = interaction.guild_id
    user_id = interaction.user.id
    guild_state = get_guild_state(guild_id)

    button_id = interaction.data.get("custom_id")
    logger.info(f"Button clicked: {button_id} by user: {user_id}")

    if guild_state.current_song:
        requester_id = guild_state.current_song.get("requester_id")

        voice_channel = guild_state.voice_client.channel
        user_count = (
            len([member for member in voice_channel.members if not member.bot])
            if voice_channel
            else 0
        )
        required_votes = 2 if user_count > 1 else 1

        if button_id == "play_pause_button":
            if user_id == requester_id:
                await toggle_pause(guild_state)
            else:
                vote_passed = guild_state.add_pause_vote(user_id, required_votes)
                if vote_passed:
                    await toggle_pause(guild_state)
                else:
                    await add_reaction(
                        guild_state.now_playing_message,
                        PAUSE_EMOJI,
                        len(guild_state.pause_votes),
                    )

        elif button_id == "skip_button":
            if user_id == requester_id:
                await skip_song(guild_state)
            else:
                vote_passed = guild_state.add_skip_vote(user_id, required_votes)
                if vote_passed:
                    await skip_song(guild_state)
                else:
                    await add_reaction(
                        guild_state.now_playing_message,
                        SKIP_EMOJI,
                        len(guild_state.skip_votes),
                    )


async def toggle_pause(guild_state) -> None:
    """
    Toggles the pause state of the current song.

    Args:
        guild_state (GuildMusicState): The current guild's music state.
    """
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
    guild_state.reset_votes()


async def skip_song(guild_state) -> None:
    """
    Skips the current song.

    Args:
        guild_state (GuildMusicState): The current guild's music state.
    """
    try:
        if guild_state.voice_client.is_playing() or guild_state.is_paused:
            guild_state.voice_client.stop()
    except Exception as e:
        logger.error(f"Error occurred while trying to stop the voice client: {e}")    
    else:    
        guild_state.is_paused = False
        guild_state.skip_event.set()
        logger.info("Skipped song.")
    finally:    
        guild_state.reset_votes()



async def add_reaction(message: discord.Message, emoji: str, count: int) -> None:
    """
    Adds or updates a reaction with the vote count.

    Args:
        message (discord.Message): The message to add the reaction to.
        emoji (str): The emoji to use for the reaction.
        count (int): The number of votes to display.
    """
    for reaction in message.reactions:
        if reaction.emoji == emoji:
            await message.clear_reaction(emoji)
            break
    await message.add_reaction(emoji)
    for _ in range(count - 1):
        await message.add_reaction(emoji)


async def on_interaction(interaction: discord.Interaction, get_guild_state) -> None:
    """
    Handles interactions, specifically button clicks, and delegates to the appropriate handler.

    :param interaction: The interaction object representing the event.
    :param get_guild_state: A function to retrieve the current guild's music state.
    """
    logger.info(f"Interaction received: {interaction.data.get('custom_id')}")
    if interaction.type == discord.InteractionType.component:
        try:
            await interaction.response.defer()
        except Exception as e:
            logger.error(f"Failed to defer interaction: {e}")
            return
        await handle_button_click(interaction, get_guild_state)
