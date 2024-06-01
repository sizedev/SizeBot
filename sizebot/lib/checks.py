from discord import Member
from discord.ext import commands

from sizebot.lib.types import BotContext


def is_mod():
    async def predicate(ctx: BotContext) -> bool:
        if not isinstance(ctx.author, Member):
            return False
        if await ctx.bot.is_owner(ctx.author):
            return True
        if ctx.channel.permissions_for(ctx.author).manage_guild:
            return True
        return False
    return commands.check(predicate)
