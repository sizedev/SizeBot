import logging
import re
from datetime import datetime, timedelta

from discord.ext import commands

from sizebot.lib import utils, paths
from sizebot.lib.constants import ids

logger = logging.getLogger("sizebot")

winkPattern = re.compile(r"(; *\)|:wink:|😉)")  # Only compile regex once, to improve performance
starttime = datetime(2019, 9, 15)
milestones = [1000, 2500, 4200, 5000, 6000, 6666, 6969, 7500, 9001, 10000, 25000, 42000, 50000, 69000, 75000, 100000]


def get_winks():
    try:
        with open(paths.winkpath, "r") as f:
            winkcount = int(f.read())
    except (FileNotFoundError, ValueError):
        winkcount = 0
    return winkcount


def add_winks(count = 1):
    winkcount = get_winks()
    winkcount += count
    with open(paths.winkpath, "w") as winkfile:
        winkfile.write(str(winkcount))
    return winkcount


def count_winks(s):
    return len(winkPattern.findall(s))


async def say_milestone(channel, winkcount):
    now = datetime.today()
    timesince = now - starttime
    prettytimesince = utils.pretty_time_delta(timesince.total_seconds())
    timeperwink = timesince / winkcount
    prettytimeperwink = utils.pretty_time_delta(timeperwink.total_seconds())
    winksperday = winkcount / (timesince / timedelta(days = 1))

    await channel.send(
        f":confetti_ball: Yukio has winked **{winkcount}** times since 15 September, 2019! :wink: :confetti_ball:\n"
        f"It took **{prettytimesince}** to hit this milestone!\n"
        f"That's an average of **{prettytimeperwink}** per wink!\n"
        f"(That's **{winksperday:.4f}** winks/day!)\n"
        f"Great winking, <@{ids.yukio}>!"
    )

    logger.error(
        f"Yukio has winked {winkcount} times since 15 September, 2019! :wink:\n"
        f"It took {prettytimesince} to hit this milestone!\n"
        f"That's an average of {prettytimeperwink} per wink!\n"
        f"(That's {winksperday} winks/day!)"
    )


class WinksCog(commands.Cog):
    """Yukio wink count."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != ids.yukio:
            return

        winksSeen = count_winks(message.content)
        if winksSeen == 0:
            return

        winkcount = add_winks(winksSeen)
        if winkcount % 100 == 0:
            logger.info(f"Yukio has winked {winkcount} times!")
        if winkcount in milestones:
            await say_milestone(message.channel, winkcount)

    @commands.command(
        hidden = True,
        category = "misc"
    )
    async def winkcount(self, ctx: commands.Context[commands.Bot]):
        winkcount = get_winks()
        await ctx.send(f"Yukio has winked {winkcount} times since 15 September, 2019! :wink:")
        logger.info(f"Wink count requested by {ctx.author.nickname}! Current count: {winkcount} times!")


async def setup(bot: commands.Bot):
    await bot.add_cog(WinksCog(bot))
