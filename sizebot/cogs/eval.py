from discord.ext import commands
import numexpr

from sizebot import digilogger as logger
from sizebot.checks import requireAdmin


def evalexpr(expression):
    return numexpr.evaluate(expression, local_dict={}, global_dict={})


class EvalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(requireAdmin)
    async def eval(self, ctx, *, evalStr):
        await logger.info(f"{ctx.message.author.display_name} tried to eval {evalStr!r}.")
        result = evalexpr(evalStr)
        await logger.info(f"Result: {result!r}")
        await ctx.send(f"> ```{result!r}```")


# Necessary
def setup(bot):
    bot.add_cog(EvalCog(bot))
