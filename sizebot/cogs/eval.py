import pydoc

from discord.ext import commands

from sizebot import digilogger as logger
from sizebot.checks import requireAdmin
from sizebot import digiSV
from sizebot import utils


def strHelp(topic):
    return pydoc.render_doc(topic)


async def runEval(ctx, evalStr):
    glb = {"__builtins__": {"print": print, "dir": dir, "help": strHelp}, "pydoc": pydoc, "ctx": ctx, "logger": logger, "digiSV": digiSV}
    loc = {}

    evalLines = evalStr.split("\n")
    evalLines[-1] = "return " + evalLines[-1]
    fnStr = "async def __ex():\n" + "".join(f"\n    {line}" for line in evalLines)

    exec(
        fnStr,
        glb,
        loc
    )
    return await loc["__ex"]()


class EvalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(requireAdmin)
    async def eval(self, ctx, *, evalStr):
        await logger.info(f"{ctx.message.author.display_name} tried to eval {evalStr!r}.")
        try:
            result = await runEval(ctx, evalStr)
        except Exception as err:
            await logger.info(f"Error: {err}")
            await ctx.send(f"> **ERROR:** `{str(err)!r}`")
            return
        await utils.sendMessage(ctx, f"{result}")

    @commands.command()
    @commands.check(requireAdmin)
    async def evil(self, ctx, *, evalStr):
        await ctx.message.delete(delay=0)
        await logger.info(f"{ctx.message.author.display_name} tried to quietly eval {evalStr!r}.")
        try:
            await runEval(ctx, evalStr)
        except Exception as err:
            await logger.info(f"Error: {err}")
            await ctx.message.author.send(f"> **ERROR:** `{str(err)!r}`")


# Necessary
def setup(bot):
    bot.add_cog(EvalCog(bot))
