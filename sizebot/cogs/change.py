import importlib.resources as pkg_resources
import logging
import random
from sizebot.lib.versioning import release_on
from typing import Union

from discord.ext import commands, tasks

import sizebot.data
from sizebot.lib import changes, proportions, userdb, nickmanager
from sizebot.lib.diff import Diff, LimitedRate
from sizebot.lib.diff import Rate as ParseableRate
from sizebot.lib.errors import ChangeMethodInvalidException
from sizebot.lib.objs import objects
from sizebot.lib.units import Rate

logger = logging.getLogger("sizebot")


class ChangeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        changes.loadFromFile()

    @commands.Cog.listener()
    async def on_first_ready(self):
        # Don't start the change tasks until the bot is properly connected
        self.changeTask.start()

    def cog_unload(self):
        self.changeTask.cancel()

    @commands.command(
        aliases = ["c"],
        category = "change",
        usage = "<change> [rate] [stop]"
    )
    async def change(self, ctx, *, string: Union[LimitedRate, ParseableRate, Diff, str]):
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
            await nickmanager.nick_update(ctx.author)

            userdb.save(userdata)

            await ctx.send(f"User <@{userid}> is now {userdata.height:m} ({userdata.height:u}) tall.")

        elif isinstance(string, ParseableRate) or isinstance(string, LimitedRate):
            addPerSec, mulPerSec, stopSV, stopTV = Rate.parse(string.original)

            userdata = userdb.load(guildid, userid)  # Load this data but don't use it as an ad-hoc user test.

            changes.start(userid, guildid, addPerSec=addPerSec, mulPerSec=mulPerSec, stopSV=stopSV, stopTV=stopTV)

            await ctx.send(f"{ctx.author.display_name} has begun slow-changing at a rate of `{string.original}`.")

        elif string == "stop":
            await ctx.invoke(self.bot.get_command("stopchange"), query="")

    @commands.command(
        hidden = True
    )
    @commands.is_owner()
    async def changes(self, ctx):
        # PERMISSION: requires manage_messages
        await ctx.message.delete(delay=0)

        changeDump = changes.formatSummary()

        if not changeDump:
            changeDump = "No active changes"

        await ctx.author.send("**ACTIVE CHANGES**\n" + changeDump)

    @commands.command(
        aliases = ["changestop"],
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

    @commands.command(
        aliases = ["eat"],
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
        await nickmanager.nick_update(ctx.author)
        userdata = userdb.load(guildid, userid)

        lines = pkg_resources.read_text(sizebot.data, "eatme.txt").splitlines()
        line = random.choice(lines)

        await ctx.send(
            f"<@{userid}> ate a :cake:! *{line}*\n"
            f"They multiplied {randmult}x and are now {userdata.height:m} tall. ({userdata.height:u})")

    @commands.command(
        aliases = ["drink"],
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
        await nickmanager.nick_update(ctx.author)
        userdata = userdb.load(guildid, userid)

        lines = pkg_resources.read_text(sizebot.data, "drinkme.txt").splitlines()
        line = random.choice(lines)

        await ctx.send(
            f"<@{ctx.author.id}> drank a :milk:! *{line}*\n"
            f"They shrunk {randmult}x and are now {userdata.height:m} tall. ({userdata.height:u})")

    @commands.command(
        category = "change"
    )
    @commands.guild_only()
    async def pushme(self, ctx):
        """Push me!

        Increases or decreases your height by a random amount between 2x and 20x."""
        c = random.randint(1, 2)
        if c == 1:
            await ctx.invoke(self.bot.get_command("eatme"))
        else:
            await ctx.invoke(self.bot.get_command("drinkme"))

    @release_on("3.7")
    @commands.guild_only()
    async def outgrow(self, ctx):
        """Outgrows the next object in the object database."""
        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)
        objs_larger = [o for o in objects if o.unitlength > userdata.height]
        if not objs_larger:
            await ctx.send("You have nothing left to outgrow!")
            return
        obj = objs_larger[0]
        userdata.height = obj.unitlength * 1.1
        userdb.save(userdata)

        await ctx.send(f"You outgrew **{obj.name}** and are now **{userdata.height:,.3mu}** tall!")

    @release_on("3.7")
    @commands.guild_only()
    async def outshrink(self, ctx):
        """Outshrinks the next object in the object database."""
        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)
        objs_smaller = [o for o in objects if o.unitlength < userdata.height].reverse()
        if not objs_smaller:
            await ctx.send("You have nothing left to outshrink!")
            return
        obj = objs_smaller[0]
        userdata.height = obj.unitlength / 1.1
        userdb.save(userdata)

        await ctx.send(f"You outshrunk **{obj.name}** and are now **{userdata.height:,.3mu}** tall!")

    @tasks.loop(seconds=6)
    async def changeTask(self):
        """Slow growth task"""
        try:
            await changes.apply(self.bot)
        except Exception as e:
            logger.error(e)


def setup(bot):
    bot.add_cog(ChangeCog(bot))
