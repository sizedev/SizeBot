from sizebot.discordplus import bot, command, embed, member


def patch():
    embed.patch()
    command.patch()
    member.patch()
    bot.patch()
