import re
from datetime import datetime, timedelta

from discord.ext import commands

from sizebot import digilogger as logger
from sizebot import utils
from sizebot.conf import conf

winkPattern = re.compile(r"(; *\)|:wink:|😉)")  # Only compile regex once, to improve performance
starttime = datetime(2019, 9, 15)
milestones = [1000, 2500, 5000, 10000, 25000, 50000, 100000]


def getWinks():
    try:
        with open(conf.winkpath, "r") as f:
            winkcount = int(f.read())
    except (FileNotFoundError, ValueError):
        winkcount = 0
    return winkcount


def addWinks(count = 1):
    winkcount = getWinks()
    winkcount += count
    with open(conf.winkpath, "w") as winkfile:
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
    yukioid = conf.getId("Yukio")

    await channel.send(f":confetti_ball: Yukio has winked **{winkcount}** times since 15 September, 2019! :wink: :confetti_ball\n:"
                       f"It took **{prettytimesince}** to hit this milestone!\n"
                       f"That's an average of **{prettytimeperwink}** per wink!\n"
                       f"(That's **{winksperday}** winks/day!)\n"
                       f"Great winking, <@{yukioid}>!")

    logger.error(f"Yukio has winked {winkcount} times since 15 September, 2019! :wink:\n"
            f"It took {prettytimesince} to hit this milestone!\n"
            f"That's an average of {prettytimeperwink} per wink!\n"
            f"(That's {winksperday} winks/day!)")


# Commands:
class WinksCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Yukio wink count
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != conf.getId("Yukio"):
            return

        winksSeen = countWinks(message.content)
        if winksSeen == 0:
            return

        winkcount = addWinks(winksSeen)
        logger.info(f"Yukio has winked {winkcount} times!")
        if winkcount in milestones:
            await sayMilestone(message.channel, winkcount)

    @commands.command()
    async def winkcount(self, ctx):
        winkcount = getWinks()
        await ctx.send(f"Yukio has winked {winkcount} times since 15 September, 2019! :wink:")
        logger.info(f"Wink count requested! Current count: {winkcount} times!")


# Necessary
def setup(bot):
    bot.add_cog(WinksCog(bot))
