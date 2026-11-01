"""The moderation actions. The slash commands and the spam trap channel both go through here."""

import logging
from enum import StrEnum

import discord

from owlin.bot import checks

logger = logging.getLogger(__name__)


SPAM_HISTORY_SECONDS = 60 * 60
MAX_REASON_LENGTH = 512


class Outcome(StrEnum):
    DONE = "done"
    EXEMPT = "exempt"  # a bot, the owner, an administrator or a moderator
    ABOVE_BOT = "above_bot"  # the member's top role is not below the bot's
    FAILED = "failed"  # Discord refused, or the member had already left
    STILL_BANNED = "still_banned"  # the messages are gone, but the unban failed


def refusal(guild: discord.Guild, target: discord.Member) -> Outcome | None:
    """Why the bot must not touch this member, or None when it may."""
    if checks.is_exempt(target, guild):
        return Outcome.EXEMPT
    if not checks.can_act_on(guild.me, target):
        return Outcome.ABOVE_BOT
    return None


async def kick_member(guild: discord.Guild, target: discord.Member, reason: str) -> Outcome:
    blocked = refusal(guild, target)
    if blocked:
        return blocked

    try:
        await guild.kick(target, reason=reason[:MAX_REASON_LENGTH])
    except discord.HTTPException:
        logger.exception("Could not kick %s (%s)", target, target.id)
        return Outcome.FAILED

    logger.info("Kicked %s (%s): %s", target, target.id, reason)
    return Outcome.DONE


async def punish_spammer(guild: discord.Guild, target: discord.Member, reason: str) -> Outcome:
    """Kick a member and delete what they wrote in the last hour, in every channel.

    Discord can delete a member's recent messages only as part of a ban, and a kick has no such
    option. So the member is banned with their messages removed and unbanned right away, which
    leaves them off the server but free to come back.
    """
    blocked = refusal(guild, target)
    if blocked:
        return blocked

    reason = reason[:MAX_REASON_LENGTH]
    try:
        await guild.ban(target, reason=reason, delete_message_seconds=SPAM_HISTORY_SECONDS)
    except discord.HTTPException:
        logger.exception("Could not remove %s (%s) as a spammer", target, target.id)
        return Outcome.FAILED

    try:
        await guild.unban(target, reason=reason)
    except discord.HTTPException:
        logger.exception("%s (%s) was banned as a spammer but the unban failed", target, target.id)
        return Outcome.STILL_BANNED

    logger.info("Removed spammer %s (%s): %s", target, target.id, reason)
    return Outcome.DONE
