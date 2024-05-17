from discord.ext import commands


# Ignore Tupperboxes being mistaken for commands.
def ignore_tupperbox(ctx: commands.Context[commands.Bot]) -> bool:
    return not (ctx.message.content.startswith(ctx.prefix) and ctx.message.content.endswith(ctx.prefix))


async def setup(bot: commands.Bot):
    bot.add_check(ignore_tupperbox)
