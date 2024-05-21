import logging
import re
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from sizebot.lib import utils, paths
from sizebot.lib.constants import ids
from sizebot.lib.types import BotContext

logger = logging.getLogger("sizebot")

_wink_pattern = re.compile(r"(; *\)|:wink:|😉)")  # Only compile regex once, to improve performance
_starttime = datetime(2019, 9, 15)
_milestones = [1000, 2500, 4200, 5000, 6000, 6666, 6969, 7500, 9001, 10000, 25000, 42000, 50000, 69000, 75000, 100000]


def _get_winks() -> int:
    try:
        with open(paths.winkpath, "r") as f:
            winkcount = int(f.read())
    except (FileNotFoundError, ValueError):
        winkcount = 0
    return winkcount


def _add_winks(count: int = 1) -> int:
    winkcount = _get_winks()
    winkcount += count
    with open(paths.winkpath, "w") as winkfile:
        winkfile.write(str(winkcount))
    return winkcount


def _count_winks(s: str) -> int:
    return len(_wink_pattern.findall(s))


async def _say_milestone(channel: discord.TextChannel, winkcount: int):
    now = datetime.today()
    timesince = now - _starttime
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
    async def on_message(self, message: discord.Message):
        if message.author.id != ids.yukio:
            return

        winksSeen = _count_winks(message.content)
        if winksSeen == 0:
            return

        winkcount = _add_winks(winksSeen)
        if winkcount % 100 == 0:
            logger.info(f"Yukio has winked {winkcount} times!")
        if winkcount in _milestones:
            await _say_milestone(message.channel, winkcount)

    @commands.command(
        hidden = True,
        category = "misc"
    )
    async def winkcount(self, ctx: BotContext):
        winkcount = _get_winks()
        await ctx.send(f"Yukio has winked {winkcount} times since 15 September, 2019! :wink:")
        logger.info(f"Wink count requested by {ctx.author.nickname}! Current count: {winkcount} times!")


async def setup(bot: commands.Bot):
    await bot.add_cog(WinksCog(bot))
