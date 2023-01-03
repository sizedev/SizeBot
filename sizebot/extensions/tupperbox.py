# Ignore Tupperboxes being mistaken for commands.
def ignoreTupperbox(ctx):
    return not (ctx.message.content.startswith(ctx.prefix) and ctx.message.content.endswith(ctx.prefix))


async def setup(bot):
    bot.add_check(ignoreTupperbox)
