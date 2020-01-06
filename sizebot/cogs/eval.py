import discord
from discord.ext import commands

from sizebot import utils
from sizebot import digilogger as logger
from sizebot.checks import requireAdmin
from sizebot.digieval import runEval


class EvalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(requireAdmin)
    async def eval(self, ctx, *, evalStr):
        await logger.info(f"{ctx.message.author.display_name} tried to eval {evalStr!r}.")

        # Show user that bot is busy doing something
        waitMsg = None
        if isinstance(ctx.channel, discord.TextChannel):
            waitMsg = await ctx.send(f"<a:loading:663876493771800603>")

        async with ctx.typing():
            try:
                result = await runEval(ctx, evalStr)
            except Exception as err:
                await logger.error("eval error:\n" + utils.formatTraceback(err))
                await ctx.send(f"⚠️ ` {str(err)} `")
                return
            finally:
                # Remove wait message when done
                if waitMsg:
                    await waitMsg.delete(delay=0)

        await utils.sendMessage(ctx, f"{result}")

    @commands.command()
    @commands.check(requireAdmin)
    async def evil(self, ctx, *, evalStr):
        await ctx.message.delete(delay = 0)

        await logger.info(f"{ctx.message.author.display_name} tried to quietly eval {evalStr!r}.")

        async with ctx.typing():
            try:
                await runEval(ctx, evalStr, returnValue = False)
            except Exception as err:
                await logger.error("eval error:\n" + utils.formatTraceback(err))
                await ctx.message.author.send(f"⚠️ ` {str(err)} `")


# Necessary
def setup(bot):
    bot.add_cog(EvalCog(bot))
