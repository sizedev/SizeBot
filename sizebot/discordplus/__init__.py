from sizebot.discordplus import embed, command, member


def patch():
    embed.patch()
    command.patch()
    member.patch()
