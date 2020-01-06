from discord.ext import commands

from sizebot import digilogger as logger
from sizebot.checks import requireAdmin


async def runEval(ctx, evalStr):
    glb = {"__builtins__": {"print": print}}
    loc = {"ctx": ctx}
    exec(
        "async def __ex():"
        f"    return {evalStr}",
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
            print(err)
            await logger.info(f"Error: {err}")
            await ctx.send(f"> **ERROR:** `{str(err)!r}`")
            return
        await logger.info(f"Result: {result!r}")
        await ctx.send(f"> ```{result!r}```")


# Necessary
def setup(bot):
    bot.add_cog(EvalCog(bot))
