from discordplus import bot, command, embed, member, client, messageable, snowflake, tasks


def patch():
    embed.patch()
    command.patch()
    member.patch()
    bot.patch()
    client.patch()
    messageable.patch()
    snowflake.patch()
    tasks.patch()
