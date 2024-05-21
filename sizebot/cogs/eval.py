import logging
import re

import discord
from discord import Embed
from discord.ext import commands

from sizebot.lib import utils
from sizebot.lib.constants import emojis
from sizebot.lib.eval import run_eval
from sizebot.lib.types import BotContext


logger = logging.getLogger("sizebot")


class EvalCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        hidden = True,
        multiline = True
    )
    @commands.is_owner()
    async def eval(self, ctx: BotContext, *, evalStr: str):
        """Evaluate a Python expression."""
        evalStr = remove_code_block(evalStr)

        logger.info(f"{ctx.author.display_name} tried to eval {evalStr!r}.")

        # Show user that bot is busy doing something
        waitMsg = None
        if isinstance(ctx.channel, discord.TextChannel):
            waitMsg = await ctx.send(f"{emojis.run_program} Running eval... {emojis.loading}")

        async with ctx.typing():
            try:
                result = await run_eval(ctx, evalStr)
            except Exception as err:
                logger.error("eval error:\n" + utils.format_traceback(err))
                await ctx.send(emojis.warning + f" ` {format_error(err)} `")
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
    async def evil(self, ctx: BotContext, *, evalStr: str):
        """Evaluate a Python expression, but evilly."""
        # PERMISSION: requires manage_messages
        await ctx.message.delete(delay = 0)

        evalStr = remove_code_block(evalStr)

        logger.info(f"{ctx.author.display_name} tried to quietly eval {evalStr!r}.")

        async with ctx.typing():
            try:
                await run_eval(ctx, evalStr)
            except Exception as err:
                logger.error("eval error:\n" + utils.format_traceback(err))
                await ctx.author.send(emojis.warning + f" ` {format_error(err)} `")


def remove_code_block(s: str) -> str:
    re_codeblock = re.compile(r"^\s*```(?:python)?(.*)```\s*$", re.DOTALL)
    s_nocodeblock = re.sub(re_codeblock, r"\1", s)
    if s_nocodeblock != s:
        return s_nocodeblock

    re_miniblock = re.compile(r"^\s*`(.*)`\s*$", re.DOTALL)
    s_nominiblock = re.sub(re_miniblock, r"\1", s)
    if s_nominiblock != s:
        return s_nominiblock

    return s


def format_error(err: Exception) -> str:
    fullname = utils.get_fullname(err)

    errMessage = str(err)
    if errMessage:
        errMessage = f": {errMessage}"

    return f"{fullname}{errMessage}"


async def setup(bot: commands.Bot):
    await bot.add_cog(EvalCog(bot))
