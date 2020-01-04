import random
import time

from discord.ext import commands, tasks

from sizebot.digidecimal import Decimal
from sizebot import digilogger as logger
from sizebot import userdb
from sizebot import digiSV
from sizebot import digisize


class Change:
    def __init__(self, bot, userid, guildid, *, addPerSec=0, mulPerSec=1, stopSV=None, stopTV=None):
        self.bot = bot
        self.guildid = guildid
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
        mulPerTick = self.mulPerSec ** seconds
        userdata = userdb.load(self.userid)
        newheight = (userdata.height * mulPerTick) + addPerTick
        if self.stopSV is not None and ((newheight < userdata.height and self.stopSV >= newheight) or (newheight > userdata.height and self.stopSV <= newheight)):
            newheight = self.stopSV
            running = False
        userdata.height = newheight
        userdb.save(userdata)
        guild = self.bot.get_guild(self.guildid)
        member = guild.get_member(self.userid)
        await digisize.nickUpdate(member)
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
        self.changeTask.start()

    def cog_unload(self):
        self.changeTask.cancel()

    @commands.command()
    async def change(self, ctx, style, *, amount):
        # Change height
        digisize.changeUser(ctx.message.author.id, style, amount)
        userdata = userdb.load(ctx.message.author.id)
        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) changed {style}-style {amount}.")
        await ctx.send(f"User <@{ctx.message.author.id}> is now {digiSV.fromSV(userdata.height, 'm')} ({digiSV.fromSV(userdata.height, 'u')}) tall.")

    @commands.command()
    async def slowchange(self, ctx, *, rateStr: str):
        addPerSec, mulPerSec, stopSV, stopTV = digiSV.toRate(rateStr)
        key = ctx.message.author.id, ctx.message.guild.id
        change = Change(self.bot, ctx.message.author.id, ctx.message.guild.id, addPerSec=addPerSec, mulPerSec=mulPerSec, stopSV=stopSV, stopTV=stopTV)
        self.changes[key] = change
        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) slow-changed {addPerSec:+}/sec and *{mulPerSec}/sec until {stopSV and digiSV.fromSV(stopSV)} for {stopTV} seconds.")

    @commands.command()
    async def stopchange(self, ctx):
        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) stopped slow-changing.")

        key = ctx.message.author.id, ctx.message.guild.id
        deleted = self.changes.pop(key, None)

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
        runningChanges = {}
        for key, change in self.changes.items():
            try:
                running = await change.apply()
                if running:
                    runningChanges[key] = change
            except Exception as e:
                await logger.error(e)
        self.changes = runningChanges


# Necessary.
def setup(bot):
    bot.add_cog(ChangeCog(bot))
