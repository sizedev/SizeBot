from discord.ext import commands
from globalsb import yukioid
import digilogger as logger
import re

winkpath = "../winkcount.txt"
winkPattern = re.compile(r"(; *\)|:wink:|😉)")  # Only compile regex once, to improve performance


def getWinks():
    try:
        with open(winkpath, "r") as f:
            try:
                winkcount = int(f.read())
            except ValueError:
                winkcount = 0
    except FileNotFoundError:
        winkcount = 0
    return winkcount


def addWinks(count=1):
    winkcount = getWinks()
    winkcount += count
    with open(winkpath, "w") as winkfile:
        winkfile.write(str(winkcount))
    return winkcount


def countWinks(s):
    return len(winkPattern.findall(s))


# Commands for non-size stuff.
#
# Commands:
class WinksCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Yukio wink count.
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != yukioid:
            return

        winksSeen = countWinks(message.content)
        if winksSeen == 0:
            return

        winkcount = addWinks(winksSeen)
        logger.msg(f"Yukio has winked {winkcount} times!")

    @commands.command()
    async def winkcount(self, ctx):
        winkcount = getWinks()
        await ctx.send(f"Yukio has winked {winkcount} times! :wink:")
        logger.msg(f"Wink count requested: {winkcount} times!")


# Necessary.
def setup(bot):
    bot.add_cog(WinksCog(bot))
