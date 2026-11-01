import discord
from discord import app_commands
from discord.ext import commands

from owlin.bot.services import moderation
from owlin.bot.services.moderation import Outcome

REPLIES = {
    Outcome.DONE: "{name} was removed.",
    Outcome.EXEMPT: "{name} is a bot, an administrator or a moderator, so the bot leaves them alone.",
    Outcome.ABOVE_BOT: "{name} has a role that is not below the bot's role. Move the bot's role higher.",
    Outcome.FAILED: "Discord refused. The bot may lack the permission, or {name} has already left.",
    Outcome.STILL_BANNED: "{name}'s messages were deleted, but the unban failed. Unban them by hand.",
}


class Moderation(commands.Cog):
    @staticmethod
    async def _may_moderate(interaction: discord.Interaction) -> bool:
        if interaction.permissions.kick_members:
            return True
        await interaction.response.send_message("You need the Kick Members permission.", ephemeral=True)
        return False

    @staticmethod
    def _reason(interaction: discord.Interaction, command: str, reason: str | None) -> str:
        return f"/{command} by {interaction.user} ({interaction.user.id}): {reason or 'no reason given'}"

    @app_commands.command(name="spam", description="Kick a member and delete their messages from the last hour")
    @app_commands.describe(member="The spammer", reason="Shown in the audit log")
    @app_commands.guild_only()
    @app_commands.default_permissions(kick_members=True)
    async def spam(self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None) -> None:
        if not await self._may_moderate(interaction):
            return
        # Deleting messages in every channel can take longer than the 3 seconds Discord waits for a reply.
        await interaction.response.defer(ephemeral=True)
        outcome = await moderation.punish_spammer(
            interaction.guild, member, self._reason(interaction, "spam", reason)
        )
        await interaction.followup.send(REPLIES[outcome].format(name=member.display_name))

    @app_commands.command(name="kick", description="Kick a member")
    @app_commands.describe(member="The member to kick", reason="Shown in the audit log")
    @app_commands.guild_only()
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None) -> None:
        if not await self._may_moderate(interaction):
            return
        await interaction.response.defer(ephemeral=True)
        outcome = await moderation.kick_member(interaction.guild, member, self._reason(interaction, "kick", reason))
        await interaction.followup.send(REPLIES[outcome].format(name=member.display_name))
