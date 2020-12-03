from discord.ext import commands


def is_mod():
    async def predicate(ctx):
        author = ctx.author
        modness = False
        if await ctx.bot.is_owner(author):
            modness = True
        elif author.permissions_in(ctx.channel).manage_guild:
            modness = True
        return modness
    return commands.check(predicate)
