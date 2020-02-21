from discord.ext import commands

from sizebot.globalsb import *
import sizebot.digilogger as logger
import sizebot.roller


# Commands for roleplaying.
#
# Commands: roll, r
class RPCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Die rolling command
    @commands.command()
    async def roll(self, ctx, *, dString):
        logger.msg(f"{ctx.message.author.nick} rolled {dString} verbosely.")
        try:
            result = roller.roll(dString)
        except roller.RollException:
            logger.warn("Invalid roll string.")
            await ctx.send(f"Invalid roll string `{dString}`")
            return

        header = (f"{ctx.message.author.nick} rolled `{dString}`!\n"
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
        logger.msg(f"{ctx.message.author.nick} rolled {dString} non-verbosely.")
        try:
            result = roller.roll(dString)
        except roller.RollException:
            logger.warn("Invalid roll string.")
            await ctx.send(f"Invalid roll string `{dString}`")
            return

        sendstring = f"{ctx.message.author.nick} rolled `{dString}` = **{result.total}**"

        await ctx.send(sendstring)


# Necessary
def setup(bot):
    bot.add_cog(RPCog(bot))
