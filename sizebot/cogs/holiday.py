import logging

from discord.ext import commands, tasks
from datetime import datetime, time, date
from sizebot import conf

from utils import intToRoman

logger = logging.getLogger("sizebot")


class HolidayCog(commands.Cog):
    """Do stuff on holidays."""

    def __init__(self, bot):
        self.bot = bot
        self.holidayTask.start()

    def cog_unload(self):
        self.holidayTask.cancel()

    @tasks.loop(seconds=60)
    async def holidayTask(self):
        """Holiday checker"""
        now = datetime.now()
        nowtime = now.time()
        nowday = now.day()
        midnight = time(hour = 0, minute = 0)
        # Make sure our loop point is midnight.
        if nowtime != midnight:
            timeuntilmidnight = midnight - nowtime
            self.holidayTask.change_interval(seconds = timeuntilmidnight.total_seconds())
        # Holiday checks.
        newnick = conf.name
        if nowday == date(month = 1, day = 1).day():  # New Year's Day
            newnick += f" {intToRoman(int(now.year))}"
        if nowday == date(month = 3, day = 10).day():  # Digi's birthday
            newnick += " 🎉"
        if newnick != self.bot.user.nickname:
            self.bot.user.edit(username = newnick)


def setup(bot):
    bot.add_cog(HolidayCog(bot))
