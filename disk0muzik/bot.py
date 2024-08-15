import discord
import logging
import asyncio
from discord.ext import commands
from disk0muzik.config import DISCORD_TOKEN

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="/", intents=intents)


@bot.event
async def on_ready() -> None:
    logger.info(f"Logged in as {bot.user.name}")


async def load_cogs() -> None:
    # Explicitly load the single cog
    cog_name = "cogs.music"  # Replace "music" with the actual cog name if different
    try:
        await bot.load_extension(cog_name)
        logger.info(f"Loaded cog: {cog_name}")
    except Exception as e:
        logger.error(f"Failed to load cog {cog_name}: {e}")


async def main() -> None:
    await load_cogs()  # Load the cog before starting the bot
    await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
