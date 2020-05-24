import logging

import discord
from discord import Embed
from discord.ext import commands

from sizebot.lib import utils
from sizebot.lib.constants import emojis
from sizebot.lib.eval import runEval


logger = logging.getLogger("sizebot")


class EvalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        hidden = True,
        multiline = True
    )
    @commands.is_owner()
    async def eval(self, ctx, *, evalStr):
        """Evaluate a Python expression."""
        evalStr = utils.removeCodeBlock(evalStr)

        logger.info(f"{ctx.author.display_name} tried to eval {evalStr!r}.")

        # Show user that bot is busy doing something
        waitMsg = None
        if isinstance(ctx.channel, discord.TextChannel):
            waitMsg = await ctx.send(emojis.loading)

        async with ctx.typing():
            try:
                result = await runEval(ctx, evalStr)
            except Exception as err:
                logger.error("eval error:\n" + utils.formatTraceback(err))
                await ctx.send(emojis.warning + f" ` {utils.formatError(err)} `")
                return
            finally:
                # Remove wait message when done
                if waitMsg:
                    await waitMsg.delete(delay=0)

        if isinstance(result, Embed):
            await ctx.send(embed=result)
        else:
            strResult = str(result).replace("```", r"\`\`\`")
            for m in utils.chunkMsg(strResult):
                await ctx.send(m)

    @commands.command(
        hidden = True,
        multiline = True
    )
    @commands.is_owner()
    async def evil(self, ctx, *, evalStr):
        """Evaluate a Python expression, but evilly."""
        await ctx.message.delete(delay = 0)

        evalStr = utils.removeCodeBlock(evalStr)

        logger.info(f"{ctx.author.display_name} tried to quietly eval {evalStr!r}.")

        async with ctx.typing():
            try:
                await runEval(ctx, evalStr, returnValue = False)
            except Exception as err:
                logger.error("eval error:\n" + utils.formatTraceback(err))
                await ctx.author.send(emojis.warning + f" ` {utils.formatError(err)} `")


def setup(bot):
    bot.add_cog(EvalCog(bot))
