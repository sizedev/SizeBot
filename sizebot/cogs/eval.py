import logging

import discord
from discord import Embed
from discord.ext import commands

from sizebot.lib.utils import chunk_msg, format_traceback
from sizebot.lib.constants import emojis
from sizebot.lib.eval import run_eval, format_error, remove_code_block
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
    async def eval(self, ctx: BotContext, *, eval_str: str) -> None:
        """Evaluate a Python expression."""
        eval_str = remove_code_block(eval_str)

        logger.info(f"{ctx.author.display_name} tried to eval {eval_str!r}.")

        # Show user that bot is busy doing something
        wait_msg = None
        if isinstance(ctx.channel, discord.TextChannel):
            wait_msg = await ctx.send(f"{emojis.run_program} Running eval... {emojis.loading}")

        async with ctx.typing():
            try:
                result = await run_eval(ctx, eval_str)
            except Exception as err:
                logger.error("eval error:\n" + format_traceback(err))
                await ctx.send(emojis.warning + f" ` {format_error(err)} `")
                return
            finally:
                # Remove wait message when done
                if wait_msg:
                    await wait_msg.delete(delay=0)

        if isinstance(result, Embed):
            await ctx.send(embed=result)
        else:
            for m in chunk_msg(result):
                await ctx.send(m)

    @commands.command(
        hidden = True,
        multiline = True
    )
    @commands.is_owner()
    async def evil(self, ctx: BotContext, *, eval_str: str) -> None:
        """Evaluate a Python expression, but evilly."""
        # PERMISSION: requires manage_messages
        await ctx.message.delete(delay = 0)

        eval_str = remove_code_block(eval_str)

        logger.info(f"{ctx.author.display_name} tried to quietly eval {eval_str!r}.")

        try:
            await run_eval(ctx, eval_str)
        except Exception as err:
            logger.error("eval error:\n" + format_traceback(err))
            await ctx.author.send(emojis.warning + f" ` {format_error(err)} `")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EvalCog(bot))
