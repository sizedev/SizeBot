from discord.ext import commands
import numexpr

from sizebot.conf import conf
from sizebot import digilogger as logger


def isAdmin(ctx):
    return ctx.message.author.id in conf.admins


def evalexpr(expression):
    return numexpr.evaluate(expression, local_dict={}, global_dict={})


class EvalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(isAdmin)
    async def eval(self, ctx, *, evalStr):
        logger.info(f"{ctx.message.author.nick} tried to eval {evalStr!r}.")
        result = evalexpr(evalStr)
        logger.info(f"Result: {result!r}")
        ctx.send(f"> ```{result!r}```")


# Necessary
def setup(bot):
    bot.add_cog(EvalCog(bot))
