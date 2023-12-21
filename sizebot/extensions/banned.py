import discord


def den_guild_ban(ctx):
    member = ctx.author
    isMember = isinstance(member, discord.Member)
    if not isMember:
        return True
    is_guild_banned = discord.utils.get(member.roles, name = "SizeBot_Banned") is not None
    return not is_guild_banned


async def setup(bot):
    bot.add_check(den_guild_ban)
