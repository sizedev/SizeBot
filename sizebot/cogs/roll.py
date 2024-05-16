import logging

from discord.ext import commands

from sizebot.lib import roller

logger = logging.getLogger("sizebot")


class RollCog(commands.Cog):
    """Commands for dice rolling."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        aliases=["dice", "calc"],
        usage="<dice>d<sides>[d/k/dl/kh][num]",
        category = "fun"

    )
    async def roll(self, ctx: commands.Context[commands.Bot], *, dString):
        """Verbose die rolling command.

        This command is used to roll some dice.

        You can choose to keep or drop some of the dice:
        For example:
        `&roll 4d6d1` will roll 4 six-sided dice, and  ignore the result of the lowest die.
        `&roll 5d4k2` will roll 5 4-sided dice, and keep the results of the 2 highest dice.
        """
        result = roller.roll(dString)

        header = (f"{ctx.author.display_name} rolled `{dString}`!\n"
                  f"__**TOTAL: {result.total}**__\n")
        rollstrings = []
        for i, r in enumerate(result.rolls):
            rollheader = f"Roll {i + 1}: **{r.total}** | "
            dicestrings = []
            if r.used:
                dicestrings.append(f"{', '.join([str(u) for u in sorted(r.used)])}")
            if r.dropped:
                dicestrings.append(f"~~{', '.join([str(d) for d in sorted(r.dropped)])}~~")
            rollstrings.append(rollheader + ", ".join(dicestrings))

        sendstring = header + "\n".join(rollstrings)

        await ctx.send(sendstring)

    @commands.command(
        usage="<dice>d<sides>[d/k/dl/kh][num]",
        category = "fun"
    )
    async def r(self, ctx: commands.Context[commands.Bot], *, dString):
        """Simplified die rolling command.

        This command is used to roll some dice.

        You can choose to keep or drop some of the dice:
        For example:
        `&r 4d6d1` will roll 4 six-sided dice, and  ignore the result of the lowest die.
        `&r 5d4k2` will roll 5 4-sided dice, and keep the results of the 2 highest dice."""
        result = roller.roll(dString)
        await ctx.send(f"{ctx.author.display_name} rolled `{dString}` = **{result.total}**")


async def setup(bot: commands.Bot):
    await bot.add_cog(RollCog(bot))
