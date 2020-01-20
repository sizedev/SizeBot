# Ignore Tupperboxes being mistaken for commands.
def ignoreTupperbox(ctx):
    return not (ctx.message.content.startswith("&") and ctx.message.content.endswith("&"))


def setup(bot):
    bot.add_check(ignoreTupperbox)
