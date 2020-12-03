import logging
import random
from sizebot.lib.errors import ChangeMethodInvalidException
from typing import Union

from discord.ext import commands, tasks

from sizebot.lib import changes, proportions, userdb
from sizebot.lib.diff import Diff, LimitedRate
from sizebot.lib.diff import Rate as ParseableRate
from sizebot.lib.units import Rate

logger = logging.getLogger("sizebot")


class ChangeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        changes.loadFromFile()
        self.changeTask.start()

    def cog_unload(self):
        self.changeTask.cancel()

    @commands.command(
        category = "change",
        usage = "<change> [rate] [stop]"
    )
    async def change(self, ctx, *, string: Union[LimitedRate, ParseableRate, Diff]):
        """Either change or slow-change your height.

        Can be used in essentially the three following ways:
        `&change <amount>`
        `&change <amount>/<time>`
        `&change <amount>/<time> until <size/time>`

        Examples:
        `&change +1ft`
        `&change *2`
        `&change 50ft/day`
        `&change -1in/min until 1ft`
        `&change -1mm/sec for 1hr`
        """
        guildid = ctx.guild.id
        userid = ctx.author.id

        if isinstance(string, Diff):
            style = string.changetype
            amount = string.amount

            userdata = userdb.load(guildid, userid)
            if style == "add":
                userdata.height += amount
            elif style == "multiply":
                userdata.height *= amount
            elif style == "power":
                userdata = userdata ** amount
            else:
                raise ChangeMethodInvalidException
            await proportions.nickUpdate(ctx.author)

            userdb.save(userdata)

            logger.info(f"User {userid} ({ctx.author.display_name}) changed {style}-style {amount}.")
            await ctx.send(f"User <@{userid}> is now {userdata.height:m} ({userdata.height:u}) tall.")

        elif isinstance(string, ParseableRate) or isinstance(string, LimitedRate):
            addPerSec, mulPerSec, stopSV, stopTV = Rate.parse(string.original)

            userdata = userdb.load(guildid, userid)  # Load this data but don't use it as an ad-hoc user test.

            changes.start(userid, guildid, addPerSec=addPerSec, mulPerSec=mulPerSec, stopSV=stopSV, stopTV=stopTV)

            await ctx.send(f"{ctx.author.display_name} has begun slow-changing at a rate of `{string.original}`.")
            logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) slow-changed {addPerSec}/sec and *{mulPerSec}/sec until {stopSV} for {stopTV} seconds.")

    @commands.command(
        hidden = True
    )
    @commands.is_owner()
    async def changes(self, ctx):
        await ctx.message.delete(delay=0)

        changeDump = changes.formatSummary()

        if not changeDump:
            changeDump = "No active changes"

        await ctx.author.send("**ACTIVE CHANGES**\n" + changeDump)
        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) dumped the running changes.")

    @commands.command(
        category = "change"
    )
    @commands.guild_only()
    async def stopchange(self, ctx):
        """Stop a currently active slow change."""
        userid = ctx.author.id
        guildid = ctx.guild.id

        deleted = changes.stop(userid, guildid)

        if deleted is None:
            await ctx.send("You can't stop slow-changing, as you don't have a task active!")
            logger.warn(f"User {ctx.author.id} ({ctx.author.display_name}) tried to stop slow-changing, but there didn't have a task active.")
        else:
            await ctx.send(f"{ctx.author.display_name} has stopped slow-changing.")
            logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) stopped slow-changing.")

    @commands.command(
        category = "change"
    )
    @commands.guild_only()
    async def eatme(self, ctx):
        """Eat me!

        Increases your height by a random amount between 2x and 20x."""
        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)
        randmult = round(random.randint(2, 20), 1)
        proportions.changeUser(guildid, userid, "multiply", randmult)
        await proportions.nickUpdate(ctx.author)
        userdata = userdb.load(guildid, userid)

        # TODO: Randomize the italics message here
        await ctx.send(
            f"<@{userid}> ate a :cake:! *I mean it said \"Eat me...\"*\n"
            f"They multiplied {randmult}x and are now {userdata.height:m} tall. ({userdata.height:u})")
        logger.info(f"User {userid} ({ctx.author.display_name}) ate a cake and multiplied {randmult}.")

    @commands.command(
        category = "change"
    )
    @commands.guild_only()
    async def drinkme(self, ctx):
        """Drink me!

        Decreases your height by a random amount between 2x and 20x."""
        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)
        randmult = round(random.randint(2, 20), 1)
        proportions.changeUser(guildid, ctx.author.id, "divide", randmult)
        await proportions.nickUpdate(ctx.author)
        userdata = userdb.load(guildid, userid)

        # TODO: Randomize the italics message here
        await ctx.send(
            f"<@{ctx.author.id}> ate a :milk:! *I mean it said \"Drink me...\"*\n"
            f"They shrunk {randmult}x and are now {userdata.height:m} tall. ({userdata.height:u})")
        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) drank a potion and shrunk {randmult}.")

    @tasks.loop(seconds=6)
    async def changeTask(self):
        """Slow growth task"""
        await changes.apply(self.bot)


def setup(bot):
    bot.add_cog(ChangeCog(bot))
