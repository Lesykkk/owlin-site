from unittest.mock import AsyncMock, call

import pytest

from owlin.bot.client import OwlinBot
from owlin.core.config import Settings

GUILD_ID = 1


@pytest.mark.asyncio
async def test_commands_exist_on_the_server_only() -> None:
    settings = Settings(discord_bot_token="token", discord_guild_id=GUILD_ID, _env_file=None)
    bot = OwlinBot(settings)
    bot.tree.sync = AsyncMock()

    await bot.setup_hook()

    assert bot.tree.get_commands() == []
    assert {command.name for command in bot.tree.get_commands(guild=bot.guild_object)} == {"spam", "kick"}
    # The empty global list is synced too, which deletes global copies left from earlier runs.
    assert bot.tree.sync.await_args_list == [call(), call(guild=bot.guild_object)]
    await bot.close()
