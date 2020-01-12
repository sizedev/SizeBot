from discord.ext import commands
from sizebot.discordplus import commandsplus

from sizebot import digilogger as logger
from sizebot import roller


class RollCog(commands.Cog):
    """Commands for dice rolling"""
    def __init__(self, bot):
        self.bot = bot

    @commandsplus.command(aliases=["dice", "calc"], description="This description shows up first", usage="4d4 + 3d6 - 2")
    async def roll(self, ctx, *, dString):
        """Verbose die rolling command
        
        This command is used to roll some dice.
        Example: .roll 4d4 + 3d6 - 2
        """
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

    @commandsplus.command()
    async def r(self, ctx, *, dString):
        """Simplified die rolling command"""
        await logger.info(f"{ctx.message.author.display_name} rolled {dString} non-verbosely.")
        result = roller.roll(dString)
        await ctx.send(f"{ctx.message.author.display_name} rolled `{dString}` = **{result.total}**")


def setup(bot):
    bot.add_cog(RollCog(bot))
