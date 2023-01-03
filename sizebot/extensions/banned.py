import discord


def denyGuildBan(ctx):
    member = ctx.author
    isMember = isinstance(member, discord.Member)
    if not isMember:
        return True
    isGuildBanned = discord.utils.get(member.roles, name = "SizeBot_Banned") is not None
    return not isGuildBanned


async def setup(bot):
    bot.add_check(denyGuildBan)
