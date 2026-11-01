import logging

import discord
from discord.ext import commands

from owlin.bot.services import moderation

logger = logging.getLogger(__name__)


class SpamTrap(commands.Cog):
    """Nobody should write in the trap channel, so whoever does is treated as a spammer."""

    def __init__(self, channel_id: int) -> None:
        self.channel_id = channel_id

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.channel.id != self.channel_id or not isinstance(message.author, discord.Member):
            return

        outcome = await moderation.punish_spammer(
            message.guild, message.author, f"Wrote in the spam trap channel #{message.channel}"
        )
        if outcome is not moderation.Outcome.EXEMPT:
            logger.info("Spam trap caught %s (%s): %s", message.author, message.author.id, outcome)
