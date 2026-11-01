"""Runs the bot alone, without the API: `uv run python -m owlin.bot`."""

import asyncio

from owlin.bot.runner import configure_logging, run_forever
from owlin.core.config import get_settings


def main() -> None:
    settings = get_settings()
    if not settings.discord_bot_enabled:
        raise SystemExit("Set DISCORD_BOT_TOKEN and DISCORD_GUILD_ID first")

    configure_logging()
    asyncio.run(run_forever(settings))


if __name__ == "__main__":
    main()
