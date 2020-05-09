import logging
from datetime import datetime, time, timedelta

import discord
from discord.ext import commands, tasks
from discord.utils import sleep_until

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
            logger.info("Checking for holidays")

            now = datetime.now()

            # Holiday checks.
            newnick = conf.name
            newactivityname = conf.activity

            if now.month == 1 and now.day == 1:  # New Year's Day
                logger.debug("Happy new year!")
                newnick += f" {intToRoman(int(now.year))}"
                newactivityname = "Happy New Year!"
            elif now.month == 3 and now.day == 10:  # Digi's birthday
                logger.debug("Happy birthday Digi!")
                newnick += " 🎉"
                newactivityname = "Happy Birthday, DigiDuncan!"
            elif now.month == 2 and now.day == 8:  # Natalie's birthday
                logger.debug("Happy birthday Natalie!")
                newnick += " 🎉"
                newactivityname = "Happy Birthday, Natalie!"
            elif now.month == 10 and now.day == 31:  # Halloween
                logger.debug("Happy Halloween!")
                newnick = "SpookBot 🎃"
                newactivityname = "OoOoOoOo"
            elif now.month == 12 and now.day == 25:  # Christmas
                logger.debug("Merry Christmas!")
                newnick = "SizeSanta 🎄"
                newactivityname = "Merry Christmas!"
            else:
                logger.info("Just another boring non-holiday...")

            for guild in self.bot.guilds:
                if newnick != guild.me.display_name:
                    logger.info(f"Updating bot nick to \"{newnick}\" in {guild.name}.")
                    await guild.me.edit(nick = newnick)
            if newactivityname != self.bot.guilds[0].get_member(self.bot.user.id).activity:
                logger.info(f"Updating bot activity to \"{newactivityname}\".")
                newactivity = discord.Game(name = newactivityname)
                await self.bot.change_presence(activity = newactivity)

            midnight = datetime.combine(now, time(hour = 0, minute = 0, second = 0))
            next_midnight = midnight + timedelta(days = 1)
            await sleep_until(next_midnight)

        except Exception as err:
            logger.error(formatTraceback(err))

    @holidayTask.before_loop
    async def before_holidayTask(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(HolidayCog(bot))
