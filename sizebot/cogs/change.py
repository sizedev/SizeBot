import random
import time

from discord.ext import commands, tasks

from sizebot.digidecimal import Decimal
from sizebot import digilogger as logger
from sizebot import userdb
from sizebot import digiSV
from sizebot import digisize


class Change:
    def __init__(self, userid, *, addPerSec=0, mulPerSec=1, stopSV=None, stopTV=None):
        self.userid = userid
        self.addPerSec = addPerSec
        self.mulPerSec = mulPerSec
        self.stopSV = stopSV
        self.stopTV = stopTV
        self.startTime = Decimal(time.time())
        self.lastRan = self.startTime

    async def apply(self):
        running = True
        now = Decimal(time.time())
        if self.endtime is not None and self.endtime <= now:
            now = self.endtime
            running = False
        seconds = now - self.lastRan
        self.lastRan = now
        addPerTick = self.addPerSec * seconds
        mulPerTick = self.mulPerTick ** seconds
        user = userdb.load(self.userid)
        newheight = (user.height * mulPerTick) + addPerTick
        if self.stopSV is not None and ((newheight < user.height and self.stopSV >= newheight) or (newheight > user.height and self.stopSV <= newheight)):
            newheight = self.stopSV
            running = False
        user.height = newheight
        userdb.save()
        await digisize.nickUpdate(self.userid)
        return running

    @property
    def endtime(self):
        if self.stopTV is None:
            return None
        return self.startTime + self.stopTV


class ChangeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.changes = dict()

    @commands.command()
    async def change(self, ctx, style, *, amount):
        # Change height
        digisize.changeUser(ctx.message.author.id, style, amount)
        userdata = userdb.load(ctx.message.author.id)
        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) changed {style}-style {amount}.")
        await ctx.send(f"User <@{ctx.message.author.id}> is now {digiSV.fromSV(userdata.height, 'm')} ({digiSV.fromSV(userdata.height, 'u')}) tall.")

    # TODO: Switch to digisize.changeUser()
    @commands.command()
    async def slowchange(self, ctx, style: str, rate: str):
        # TODO: calculate these from rate?
        amount = ""
        delay = ""
        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) slow-changed {style}-style {amount} every {delay} minutes.")

        change = Change(ctx.message.author.id, addPerSec=0, mulPerSec=1)

        self.changes[ctx.message.author.id] = change

    @commands.command()
    async def stopchange(self, ctx):
        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) stopped slow-changing.")

        deleted = self.changes.pop(ctx.message.author.id, None)

        if deleted is None:
            await ctx.send("You can't stop slow-changing, as you don't have a task active!")
            await logger.warn(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) tried to stop slow-changing, but there didn't have a task active.")

    @commands.command()
    async def eatme(self, ctx):
        # Eat me!
        randmult = round(random.random(2, 20), 1)
        digisize.changeUser(ctx.message.author.id, "multiply", randmult)
        userdata = userdb.load(ctx.message.author.id)
        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) ate a cake and multiplied {randmult}.")
        # TODO: Randomize the italics message here
        await ctx.send(
            f"<@{ctx.message.author.id}> ate a :cake:! *I mean it said \"Eat me...\"*\n"
            f"They multiplied {randmult}x and are now {digiSV.fromSV(userdata.height, 'm')} tall. ({digiSV.fromSV(userdata.height, 'u')})")

    @commands.command()
    async def drinkme(self, ctx):
        # Drink me!
        userdata = userdb.load(ctx.message.author.id)
        randmult = round(random.random(2, 20), 1)
        digisize.changeUser(ctx.message.author.id, "divide", randmult)
        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) drank a potion and shrunk {randmult}.")
        # TODO: Randomize the italics message here
        await ctx.send(
            f"<@{ctx.message.author.id}> ate a :milk:! *I mean it said \"Drink me...\"*\n"
            f"They shrunk {randmult}x and are now {digiSV.fromSV(userdata.height, 'm')} tall. ({digiSV.fromSV(userdata.height, 'u')})")

    # Slow growth task
    # TODO: Does this restart if there are errors?
    @tasks.loop(seconds=6)
    async def changeTask(self):
        for change in self.changes.values():
            await change.apply()


# Necessary.
def setup(bot):
    bot.add_cog(ChangeCog(bot))
