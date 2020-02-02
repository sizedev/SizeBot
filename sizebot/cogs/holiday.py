import logging

from discord.ext import commands, tasks
from datetime import datetime, time, timedelta
from sizebot import conf

from sizebot.lib.utils import intToRoman, formatTraceback

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
        try:
            logger.debug("Checking for holidays")
            now = datetime.now()
            nowtime = now.time()
            TWENTY_FOUR_HOURS = timedelta(hours = 24)
            tomorrow = now + TWENTY_FOUR_HOURS
            midnight = time(hour = 0, minute = 0, second = 0)
            midnighttime = datetime.combine(tomorrow, midnight)

            # Make sure our loop point is midnight.
            if nowtime != midnight:
                timeuntilmidnight = midnighttime - now
                self.holidayTask.change_interval(seconds = timeuntilmidnight.total_seconds())

            # Holiday checks.
            newnick = conf.name
            if now.month == 1 and now.day == 1:  # New Year's Day
                logger.debug("Happy new year!")
                newnick += f" {intToRoman(int(now.year))}"
            elif now.month == 3 and now.day == 10:  # Digi's birthday
                logger.debug("Happy birthday Digi!")
                newnick += " 🎉"
            else:
                logger.debug("Just another boring non-holiday")

            if newnick != self.bot.user.name:
                logger.debug(f"Updating bot nick to {newnick}")
                await self.bot.user.edit(username = newnick)

        except Exception as err:
            logger.error(formatTraceback(err))

    @holidayTask.before_loop
    async def before_holidayTask(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(HolidayCog(bot))
