"""Runs the Discord bot next to the API, in the same process and event loop."""

import asyncio
import logging

import discord

from owlin.bot.client import OwlinBot
from owlin.core.config import Settings

logger = logging.getLogger(__name__)

RESTART_DELAY_SECONDS = 30
STOP_TIMEOUT_SECONDS = 10


def configure_logging() -> None:
    """Show the bot's own messages and discord.py's. Uvicorn sets up logging only for itself."""
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s:     %(name)s: %(message)s"))
    for name in ("owlin.bot", "discord"):
        logger_ = logging.getLogger(name)
        logger_.setLevel(logging.INFO)
        if not logger_.handlers:
            logger_.addHandler(handler)


async def run_forever(settings: Settings) -> None:
    """Keep the bot connected. A bot that crashes is started again, so the API never loses it silently."""
    while True:
        bot = OwlinBot(settings)
        try:
            await bot.start(settings.discord_bot_token)
        except discord.LoginFailure:
            logger.error("Discord rejected the bot token, so the bot stays off")
            return
        except Exception:
            logger.exception("The Discord bot stopped")
        finally:
            await bot.close()
        await asyncio.sleep(RESTART_DELAY_SECONDS)


def start_bot(settings: Settings) -> asyncio.Task | None:
    """Start the bot in the background. Without a token and a server id it stays off."""
    if not settings.discord_bot_enabled:
        if settings.discord_bot_token:
            logger.warning("DISCORD_BOT_TOKEN is set but DISCORD_GUILD_ID is not, so the bot stays off")
        return None

    configure_logging()
    return asyncio.create_task(run_forever(settings), name="discord-bot")


async def stop_bot(task: asyncio.Task | None) -> None:
    if task is None:
        return

    task.cancel()
    try:
        await asyncio.wait_for(task, STOP_TIMEOUT_SECONDS)
    except (asyncio.CancelledError, TimeoutError):
        pass
