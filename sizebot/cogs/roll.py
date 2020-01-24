import logging

from discord.ext import commands
from sizebot.discordplus import commandsplus

from sizebot.lib import roller

logger = logging.getLogger("sizebot")

class RollCog(commands.Cog):
    """Commands for dice rolling."""

    def __init__(self, bot):
        self.bot = bot

    @commandsplus.command(
        aliases=["dice", "calc"],
        usage="<dice>d<sides>"
    )
    async def roll(self, ctx, *, dString):
        """Verbose die rolling command.

        This command is used to roll some dice.

        You can choose to keep or drop some of the dice:
        For example:
        `&roll 4d6d1` will roll 4 six-sided dice, and  ignore the result of the lowest die.
        `&roll 5d4k2` will roll 5 4-sided dice, and keep the results of the 2 highest dice.
        """
        logger.info(f"{ctx.message.author.display_name} rolled {dString} verbosely.")
        result = roller.roll(dString)

        header = (f"{ctx.message.author.display_name} rolled `{dString}`!\n"
                  f"__**TOTAL: {result.total}**__\n")
        rollstrings = []
        for i, r in enumerate(result.rolls):
            rollheader = f"Roll {i+1}: **{r.total}** | "
            dicestrings = []
            if r.used:
                dicestrings.append(f"{', '.join([str(u) for u in r.used])}")
            if r.dropped:
                dicestrings.append(f"~~{', '.join([str(d) for d in r.dropped])}~~")
            rollstrings.append(rollheader + ", ".join(dicestrings))

        sendstring = header + "\n".join(rollstrings)

        await ctx.send(sendstring)

    @commandsplus.command(
        usage="<dice>d<sides>"
    )
    async def r(self, ctx, *, dString):
        """Simplified die rolling command.

        This command is used to roll some dice.

        You can choose to keep or drop some of the dice:
        For example:
        `&r 4d6d1` will roll 4 six-sided dice, and  ignore the result of the lowest die.
        `&r 5d4k2` will roll 5 4-sided dice, and keep the results of the 2 highest dice."""
        logger.info(f"{ctx.message.author.display_name} rolled {dString} non-verbosely.")
        result = roller.roll(dString)
        await ctx.send(f"{ctx.message.author.display_name} rolled `{dString}` = **{result.total}**")


def setup(bot):
    bot.add_cog(RollCog(bot))
