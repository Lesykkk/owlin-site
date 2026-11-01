"""Rules for who the bot may act on. They only read Discord objects, so they are easy to test."""

import discord


def is_exempt(member: discord.Member, guild: discord.Guild) -> bool:
    """Bots, the server owner, administrators and moderators are never punished."""
    permissions = member.guild_permissions
    return (
        member.bot
        or member.id == guild.owner_id
        or permissions.administrator
        or permissions.kick_members
    )


def can_act_on(bot_member: discord.Member, target: discord.Member) -> bool:
    """Discord lets a bot moderate only members whose top role is below its own."""
    return bot_member.top_role.position > target.top_role.position
