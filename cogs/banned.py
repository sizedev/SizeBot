import discord


# Disable commands for users with the SizeBot_Banned role.
def check(ctx):
    if not isinstance(ctx.channel, discord.abc.GuildChannel):
        return False

    role = discord.utils.get(ctx.author.roles, name='SizeBot_Banned')
    return role is None


# Necessary
def setup(bot):
    bot.add_check(check)
