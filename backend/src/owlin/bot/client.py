import discord
from discord.ext import commands

from owlin.bot.cogs.moderation import Moderation
from owlin.bot.cogs.spam_trap import SpamTrap
from owlin.core.config import Settings


class OwlinBot(commands.Bot):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.none()
        intents.guilds = True
        intents.guild_messages = True
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

        self.settings = settings
        self.guild_object = discord.Object(id=settings.discord_guild_id)

    async def setup_hook(self) -> None:
        await self.add_cog(Moderation())
        if self.settings.discord_spam_trap_channel_id:
            await self.add_cog(SpamTrap(self.settings.discord_spam_trap_channel_id))

        self.tree.copy_global_to(guild=self.guild_object)
        await self.tree.sync(guild=self.guild_object)
