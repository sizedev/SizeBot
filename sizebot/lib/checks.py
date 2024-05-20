from discord.ext import commands
from discord.ext.commands._types import Check

from sizebot.lib.types import BotContext


def is_mod() -> Check[BotContext]:
    async def predicate(ctx: BotContext) -> bool:
        author = ctx.author
        modness = False
        if await ctx.bot.is_owner(author):
            modness = True
        elif author.permissions_in(ctx.channel).manage_guild:
            modness = True
        return modness
    return commands.check(predicate)
