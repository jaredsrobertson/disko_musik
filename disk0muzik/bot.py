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


async def load_extensions() -> None:
    initial_extensions = ["cogs.music"]
    for extension in initial_extensions:
        await bot.load_extension(extension)


async def main() -> None:
    await load_extensions()
    await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
