import discord
from discord.ext import commands

from sizebot.lib.types import BotContext


def den_guild_ban(ctx: BotContext) -> bool:
    member = ctx.author
    isMember = isinstance(member, discord.Member)
    if not isMember:
        return True
    is_guild_banned = discord.utils.get(member.roles, name = "SizeBot_Banned") is not None
    return not is_guild_banned


async def setup(bot: commands.Bot):
    bot.add_check(den_guild_ban)
