import re
from datetime import timedelta, datetime

from discord.ext import commands

from sizebot.globalsb import yukioid, pretty_time_delta, digiid
import sizebot.digilogger as logger

winkpath = "../winkcount.txt"
winkPattern = re.compile(r"(; *\)|:wink:|😉)")  # Only compile regex once, to improve performance
starttime = datetime(2019, 9, 15)
milestones = [1111, 2500, 5000, 10000, 25000, 50000, 100000]


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


async def sayMilestone(message, winkcount):
    now = datetime.today()
    timesince = now - starttime
    timeperwink = timesince / winkcount
    await message.channel.send(f""":confetti_ball: Yukio has winked **{winkcount}** times since 15 September, 2019! :wink: :confetti_ball:
It took **{pretty_time_delta(timesince.total_seconds())}** to hit this milestone!
That's an average of **{pretty_time_delta(timeperwink.total_seconds())}** per wink!
(That's **{winkcount / (timesince / timedelta(days = 1))}** winks/day!)
Great winking, <@{yukioid}>!""")
    logger.crit(f"""SEE #{message.channel.name}!
Yukio has winked {winkcount} times since 15 September, 2019! :wink:
It took {pretty_time_delta(timesince.total_seconds())} to hit this milestone!
That's an average of {pretty_time_delta(timeperwink.total_seconds())} per wink!
(That's {winkcount / (timesince / timedelta(days = 1))} winks/day!)""")


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
        if winkcount in milestones:
            await sayMilestone(message, winkcount)
            await self.bot.get_user(digiid).send("MILESTONE IN #{message.channel.name}")

    @commands.command()
    async def winkcount(self, ctx):
        winkcount = getWinks()
        await ctx.send(f"Yukio has winked {winkcount} times since 15 September, 2019! :wink:")
        logger.msg(f"Wink count requested! Current count: {winkcount} times!")


# Necessary.
def setup(bot):
    bot.add_cog(WinksCog(bot))
