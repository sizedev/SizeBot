import importlib.resources as pkg_resources
import logging

import arrow

import discord
from discord.ext import commands, tasks
from discord.utils import sleep_until

import sizebot.data
from sizebot.conf import conf
from sizebot.lib.utils import int_to_roman, format_traceback

logger = logging.getLogger("sizebot")

alreadyclaimed = set()

gifts = pkg_resources.read_text(sizebot.data, "gifts.txt").splitlines()
gifts = [x.strip() for x in gifts]


class HolidayCog(commands.Cog):
    """Do stuff on holidays."""

    def __init__(self, bot):
        self.bot = bot
        self.holidayTask.start()

    def cog_unload(self):
        self.holidayTask.cancel()

    # TODO: CamelCase
    @tasks.loop(seconds=60)
    async def holidayTask(self):
        """Holiday checker"""
        try:
            # logger.info("Checking for holidays")

            now = arrow.now()

            # Holiday checks.
            newactivityname = conf.activity

            if now.month == 1 and now.day == 1:  # New Year's Day
                logger.info("Happy new year!")
                newactivityname = f"Happy New Year {int_to_roman(int(now.year))}!"
            elif now.month == 1 and now.day == 31:
                newactivityname = "Happy Birthday, Nichole!"
            elif now.month == 2 and now.day == 14:  # Valentine's Day (and Aria's birthday)
                logger.info("Happy Valentine's Day!")
                newactivityname = "Happy Valentine's Day!"
            elif now.month == 2 and now.day == 25:
                newactivityname = "Happy Birthday, Slim!"
            elif now.month == 3 and now.day == 10:  # Digi's birthday
                logger.info("Happy birthday Digi!")
                newactivityname = "Happy Birthday, DigiDuncan!"
            elif now.month == 2 and now.day == 8:  # Natalie's birthday
                logger.info("Happy birthday Natalie!")
                newactivityname = "Happy Birthday, Natalie!"
            elif now.month == 5 and now.day == 5:  # Cinco de Mayo
                logger.info("Happy Cinco de Mayo!")
                newactivityname = "Happy Cinco De Mayo!"
            elif now.month == 6 and now.day == 6:  # Swedish Independence Day
                logger.info("Happy Swedish Independence Day!")
                newactivityname = "🇸🇪 AGGA 🇸🇪"
            elif now.month == 7 and now.day == 1:  # Canada Day
                logger.info("Happy Canada Day!")
                newactivityname = "Happy Canada Day!"
            elif now.month == 7 and now.day == 4:  # Fourth of July
                logger.info("Happy Fourth of July!")
            elif now.month == 10 and now.day == 31:  # Halloween
                logger.info("Happy Halloween!")
                newactivityname = "OoOoOoOo"
            elif now.month == 12 and now.day == 25:  # Christmas
                logger.info("Merry Christmas!")
                newactivityname = "Merry Christmas!"
            else:
                # logger.info("Just another boring non-holiday...")
                pass

            if self.bot.activity and newactivityname != self.bot.activity.name:
                logger.info(f"Updating bot activity to \"{newactivityname}\".")
                newactivity = discord.Game(name = newactivityname)
                await self.bot.change_presence(activity = newactivity)

            next_midnight = arrow.get(now).replace(hour=0, minute=0, second=0).shift(days=1)
            await sleep_until(next_midnight.datetime)
        except Exception as err:
            logger.error(format_traceback(err))

    @holidayTask.before_loop
    async def before_holidayTask(self):
        await self.bot.wait_until_ready()

    @commands.command(
        hidden = True
    )
    async def secretsanta(self, ctx):
        now = arrow.now()
        if not (now.month == 12 and (24 <= now.day <= 31)):
            await ctx.send("The Secret Santa event is over! See you next Christmas season!")
            return
        userid = ctx.message.author.id
        usergift = gifts[(userid + now.year) % len(gifts)]
        output = f"<@{userid}> opened up their Secret Santa gift...\n"
        output += f"It was... {usergift}"
        if userid in alreadyclaimed:
            output += "\n*Opening the gift again doesn't change what's inside it!*"
        await ctx.send(output)
        logger.info(f"{ctx.message.author.nick} ({ctx.message.author.id}) opened their gift!")
        alreadyclaimed.add(userid)


async def setup(bot):
    await bot.add_cog(HolidayCog(bot))
