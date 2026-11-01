from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from owlin.bot.cogs.spam_trap import SpamTrap
from owlin.bot.services import moderation
from owlin.bot.services.moderation import Outcome

TRAP_CHANNEL_ID = 555


def make_member(*, member_id=100, bot=False, position=1, administrator=False, kick_members=False):
    member = MagicMock(spec=discord.Member)
    member.id = member_id
    member.bot = bot
    member.top_role = SimpleNamespace(position=position)
    member.guild_permissions = SimpleNamespace(administrator=administrator, kick_members=kick_members)
    return member


def make_guild(*, ban_error=None, unban_error=None, kick_error=None):
    guild = MagicMock()
    guild.owner_id = 1
    guild.me = make_member(member_id=2, position=10)
    guild.ban = AsyncMock(side_effect=ban_error)
    guild.unban = AsyncMock(side_effect=unban_error)
    guild.kick = AsyncMock(side_effect=kick_error)
    return guild


def refused() -> discord.HTTPException:
    return discord.HTTPException(MagicMock(status=403, reason="Forbidden"), "Missing Permissions")


@pytest.mark.asyncio
class TestPunishSpammer:
    async def test_bans_with_the_last_hour_deleted_and_unbans_at_once(self) -> None:
        guild, target = make_guild(), make_member()

        outcome = await moderation.punish_spammer(guild, target, "spam")

        assert outcome is Outcome.DONE
        guild.ban.assert_awaited_once_with(target, reason="spam", delete_message_seconds=3600)
        guild.unban.assert_awaited_once_with(target, reason="spam")

    @pytest.mark.parametrize(
        "target",
        [make_member(administrator=True), make_member(kick_members=True), make_member(bot=True)],
        ids=["administrator", "moderator", "bot"],
    )
    async def test_leaves_exempt_members_alone(self, target) -> None:
        guild = make_guild()

        outcome = await moderation.punish_spammer(guild, target, "spam")

        assert outcome is Outcome.EXEMPT
        guild.ban.assert_not_awaited()

    async def test_leaves_members_with_a_role_above_the_bot_alone(self) -> None:
        guild = make_guild()

        outcome = await moderation.punish_spammer(guild, make_member(position=10), "spam")

        assert outcome is Outcome.ABOVE_BOT
        guild.ban.assert_not_awaited()

    async def test_reports_a_refused_ban_and_does_not_unban(self) -> None:
        guild = make_guild(ban_error=refused())

        outcome = await moderation.punish_spammer(guild, make_member(), "spam")

        assert outcome is Outcome.FAILED
        guild.unban.assert_not_awaited()

    async def test_reports_a_member_who_stays_banned(self) -> None:
        guild = make_guild(unban_error=refused())

        outcome = await moderation.punish_spammer(guild, make_member(), "spam")

        assert outcome is Outcome.STILL_BANNED

    async def test_cuts_a_long_reason_to_what_discord_accepts(self) -> None:
        guild = make_guild()

        await moderation.punish_spammer(guild, make_member(), "x" * 1000)

        assert len(guild.ban.await_args.kwargs["reason"]) == moderation.MAX_REASON_LENGTH


@pytest.mark.asyncio
class TestKickMember:
    async def test_kicks_without_banning(self) -> None:
        guild, target = make_guild(), make_member()

        outcome = await moderation.kick_member(guild, target, "rude")

        assert outcome is Outcome.DONE
        guild.kick.assert_awaited_once_with(target, reason="rude")
        guild.ban.assert_not_awaited()

    async def test_leaves_exempt_members_alone(self) -> None:
        guild = make_guild()

        outcome = await moderation.kick_member(guild, make_member(administrator=True), "rude")

        assert outcome is Outcome.EXEMPT
        guild.kick.assert_not_awaited()

    async def test_reports_a_refused_kick(self) -> None:
        guild = make_guild(kick_error=refused())

        outcome = await moderation.kick_member(guild, make_member(), "rude")

        assert outcome is Outcome.FAILED


def make_message(author, channel_id: int, guild) -> MagicMock:
    message = MagicMock()
    message.author = author
    message.guild = guild
    message.channel.id = channel_id
    return message


@pytest.mark.asyncio
class TestSpamTrap:
    async def test_removes_whoever_writes_in_the_trap_channel_like_the_spam_command(self) -> None:
        guild, author = make_guild(), make_member()

        await SpamTrap(TRAP_CHANNEL_ID).on_message(make_message(author, TRAP_CHANNEL_ID, guild))

        guild.ban.assert_awaited_once()
        assert guild.ban.await_args.kwargs["delete_message_seconds"] == 3600
        guild.unban.assert_awaited_once()

    async def test_ignores_other_channels(self) -> None:
        guild = make_guild()

        await SpamTrap(TRAP_CHANNEL_ID).on_message(make_message(make_member(), TRAP_CHANNEL_ID + 1, guild))

        guild.ban.assert_not_awaited()

    async def test_ignores_administrators_in_the_trap_channel(self) -> None:
        guild = make_guild()
        admin = make_member(administrator=True)

        await SpamTrap(TRAP_CHANNEL_ID).on_message(make_message(admin, TRAP_CHANNEL_ID, guild))

        guild.ban.assert_not_awaited()

    async def test_ignores_authors_who_are_not_members(self) -> None:
        guild = make_guild()
        webhook_author = MagicMock(spec=discord.User)

        await SpamTrap(TRAP_CHANNEL_ID).on_message(make_message(webhook_author, TRAP_CHANNEL_ID, guild))

        guild.ban.assert_not_awaited()
