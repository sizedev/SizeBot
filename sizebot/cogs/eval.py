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
    async def eval(self, ctx: commands.Context, *, evalStr):
        """Evaluate a Python expression."""
        evalStr = utils.remove_code_block(evalStr)

        logger.info(f"{ctx.author.display_name} tried to eval {evalStr!r}.")

        # Show user that bot is busy doing something
        waitMsg = None
        if isinstance(ctx.channel, discord.TextChannel):
            waitMsg = await ctx.send(f"{emojis.run_program} Running eval... {emojis.loading}")

        async with ctx.typing():
            try:
                result = await runEval(ctx, evalStr)
            except Exception as err:
                logger.error("eval error:\n" + utils.format_traceback(err))
                await ctx.send(emojis.warning + f" ` {utils.format_error(err)} `")
                return
            finally:
                # Remove wait message when done
                if waitMsg:
                    await waitMsg.delete(delay=0)

        if isinstance(result, Embed):
            await ctx.send(embed=result)
        else:
            strResult = str(result).replace("```", r"\`\`\`")
            for m in utils.chunk_msg(strResult):
                await ctx.send(m)

    @commands.command(
        hidden = True,
        multiline = True
    )
    @commands.is_owner()
    async def evil(self, ctx: commands.Context, *, evalStr):
        """Evaluate a Python expression, but evilly."""
        # PERMISSION: requires manage_messages
        await ctx.message.delete(delay = 0)

        evalStr = utils.remove_code_block(evalStr)

        logger.info(f"{ctx.author.display_name} tried to quietly eval {evalStr!r}.")

        async with ctx.typing():
            try:
                await runEval(ctx, evalStr, returnValue = False)
            except Exception as err:
                logger.error("eval error:\n" + utils.format_traceback(err))
                await ctx.author.send(emojis.warning + f" ` {utils.format_error(err)} `")


async def setup(bot):
    await bot.add_cog(EvalCog(bot))
