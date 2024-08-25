import discord
import logging
import asyncio
from discord.ext import commands
from disk0muzik.config import DISCORD_TOKEN
from disk0muzik.utils.interaction_handler import skip_song

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="/", intents=intents)


@bot.event
async def on_ready() -> None:
    logger.info(f"Logged in as {bot.user.name}")


@bot.command()
async def force_skip(ctx: commands.Context) -> None:
    """Force skip the current song without user or vote checks. For production testing only."""
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        logger.warning(
            "Failed to delete the force_skip command message due to permissions."
        )
    except discord.HTTPException as e:
        logger.error(f"Failed to delete the force_skip command message: {e}")

    music_cog = bot.get_cog("Music")
    if music_cog is None:
        await ctx.send("Music cog is not loaded.")
        return

    guild_state = music_cog.get_guild_state(ctx.guild.id)

    if guild_state and guild_state.voice_client and guild_state.current_song:
        logger.info("Force skipping the current song.")
        await skip_song(guild_state)
    else:
        await ctx.send("No song is currently playing.")


async def load_cogs() -> None:
    cog_name = "cogs.music"
    try:
        await bot.load_extension(cog_name)
        logger.info(f"Loaded cog: {cog_name}")
    except Exception as e:
        logger.error(f"Failed to load cog {cog_name}: {e}")


async def main() -> None:
    await load_cogs()
    await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
