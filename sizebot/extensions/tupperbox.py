from sizebot import conf


# Ignore Tupperboxes being mistaken for commands.
def ignoreTupperbox(ctx):
    return not (ctx.message.content.startswith(conf.prefix) and ctx.message.content.endswith(conf.prefix))


def setup(bot):
    bot.add_check(ignoreTupperbox)
