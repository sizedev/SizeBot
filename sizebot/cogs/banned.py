from sizebot.lib.checks import denyGuildBan


def setup(bot):
    bot.add_check(denyGuildBan)
