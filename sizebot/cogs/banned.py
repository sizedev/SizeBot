import discord


def isBanned(member):
    return discord.utils.get(member.roles, name = "SizeBot_Banned") is not None


# Disable commands for users with the SizeBot_Banned role
def check(ctx):
    if not isinstance(ctx.channel, discord.abc.GuildChannel):
        return False

    return not isBanned(ctx.author)


# Necessary
def setup(bot):
    bot.add_check(check)
