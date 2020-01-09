from sizebot.checks import denyGuildBan


def setup(bot):
    bot.add_check(denyGuildBan)
