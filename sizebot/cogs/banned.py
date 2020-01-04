from sizebot.checks import denyGuildBan


# Necessary
def setup(bot):
    bot.add_check(denyGuildBan)
