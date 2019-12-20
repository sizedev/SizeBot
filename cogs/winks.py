import re
from datetime import datetime, timedelta

from discord.ext import commands

import digiformatter as df
import utils
import iddb

winkpath = "text/winkcount.txt"
winkPattern = re.compile(r"(; *\)|:wink:|😉)")  # Only compile regex once, to improve performance
starttime = datetime.datetime(2019, 9, 15)
milestones = [1000, 2500, 5000, 10000, 25000, 50000, 100000]


def getWinks():
    try:
        with open(winkpath, "r") as f:
            try:
                winkcount = int(f.read())
            except ValueError:
                winkcount = 0
    except FileNotFoundError:
        winkcount = 0
        with open(winkpath, "w") as f:
            f.write(str(winkcount))
    return winkcount


def addWinks(count = 1):
    winkcount = getWinks()
    winkcount += count
    with open(winkpath, "w") as winkfile:
        winkfile.write(str(winkcount))
    return winkcount


def countWinks(s):
    return len(winkPattern.findall(s))


async def sayMilestone(channel, winkcount):
    now = datetime.today()
    timesince = now - starttime
    prettytimesince = utils.prettyTimeDelta(timesince.total_seconds())
    timeperwink = timesince / winkcount
    prettytimeperwink = utils.prettyTimeDelta(timeperwink.total_seconds())
    winksperday = winkcount / (timesince / timedelta(days = 1))
    yukioid = iddb.getID("Yukio")

    await channel.send(f":confetti_ball: Yukio has winked **{winkcount}** times since 15 September, 2019! :wink: :confetti_ball\n:"
                       f"It took **{prettytimesince}** to hit this milestone!\n"
                       f"That's an average of **{prettytimeperwink}** per wink!\n"
                       f"(That's **{winksperday}** winks/day!)\n"
                       f"Great winking, <@{yukioid}>!")

    df.crit(f"Yukio has winked {winkcount} times since 15 September, 2019! :wink:\n"
            f"It took {prettytimesince} to hit this milestone!\n"
            f"That's an average of {prettytimeperwink} per wink!\n"
            f"(That's {winksperday} winks/day!)")


# Commands:
class WinksCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Yukio wink count.
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != iddb.getID("Yukio"):
            return

        winksSeen = countWinks(message.content)
        if winksSeen == 0:
            return

        winkcount = addWinks(winksSeen)
        df.msg(f"Yukio has winked {winkcount} times!")
        if winkcount in milestones:
            await sayMilestone(message.channel, winkcount)

    @commands.command()
    async def winkcount(self, ctx):
        winkcount = getWinks()
        await ctx.send(f"Yukio has winked {winkcount} times since 15 September, 2019! :wink:")
        df.msg(f"Wink count requested! Current count: {winkcount} times!")


# Necessary.
def setup(bot):
    bot.add_cog(WinksCog(bot))
