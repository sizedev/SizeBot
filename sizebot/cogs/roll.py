from discord.ext import commands

from sizebot import digilogger as logger
from sizebot import roller


# Commands for dice rolling
#
# Commands: roll, r
class RollCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Die rolling command
    @commands.command()
    async def roll(self, ctx, *, dString):
        await logger.info(f"{ctx.message.author.display_name} rolled {dString} verbosely.")
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

    @commands.command()
    async def r(self, ctx, *, dString):
        await logger.info(f"{ctx.message.author.display_name} rolled {dString} non-verbosely.")
        result = roller.roll(dString)
        await ctx.send(f"{ctx.message.author.display_name} rolled `{dString}` = **{result.total}**")


# Necessary
def setup(bot):
    bot.add_cog(RollCog(bot))
