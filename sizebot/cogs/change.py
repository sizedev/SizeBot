import random
import time
import json

from discord.ext import commands, tasks
from sizebot.discordplus import commandsplus

from sizebot.digidecimal import Decimal
from sizebot import digilogger as logger
from sizebot import userdb
from sizebot.digiSV import Rate, SV, TV
from sizebot import digisize
from sizebot.checks import requireAdmin
from sizebot.conf import conf


class Change:
    changes = {}

    def __init__(self, bot, userid, guildid, *, addPerSec=0, mulPerSec=1, stopSV=None, stopTV=None, startTime=None, lastRan=None):
        self.bot = bot
        self.userid = userid
        self.guildid = guildid
        self.addPerSec = addPerSec and SV(addPerSec)
        self.mulPerSec = mulPerSec and Decimal(mulPerSec)
        self.stopSV = stopSV and SV(stopSV)
        self.stopTV = stopTV and TV(stopTV)
        self.startTime = startTime and Decimal(startTime)
        self.lastRan = lastRan and Decimal(lastRan)

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

    def __str__(self):
        return f"gid:{self.guildid}/uid:{self.userid} {self.addPerSec} *{self.mulPerSec} , stop at {self.stopSV}, stop after {self.stopTV}s"

    @classmethod
    def start(cls, bot, userid, guildid, *, addPerSec=0, mulPerSec=1, stopSV=None, stopTV=None):
        """Start a new change task"""
        startTime = Decimal(time.time())
        lastRan = startTime
        cls.load(bot, userid, guildid, addPerSec=addPerSec, mulPerSec=mulPerSec, stopSV=stopSV, stopTV=stopTV, startTime=startTime, lastRan=lastRan)
        cls.saveFile(conf.changespath)

    @classmethod
    def load(cls, bot, userid, guildid, *, addPerSec=0, mulPerSec=1, stopSV=None, stopTV=None, startTime=None, lastRan=None):
        """Load a change task into memory"""
        cls.changes[userid, guildid] = Change(bot, userid, guildid, addPerSec=addPerSec, mulPerSec=mulPerSec, stopSV=stopSV, stopTV=stopTV, startTime=startTime, lastRan=lastRan)

    @classmethod
    def stop(cls, userid, guildid):
        """Stop a running change task"""
        deleted = cls.changes.pop((userid, guildid), None)
        cls.saveFile(conf.changespath)
        return deleted

    def toJson(self):
        return {
            "userid": self.userid,
            "guildid": self.guildid,
            "addPerSec": self.addPerSec and str(self.addPerSec),
            "mulPerSec": self.mulPerSec and str(self.mulPerSec),
            "stopSV": self.stopSV and str(self.stopSV),
            "stopTV": self.stopTV and str(self.stopTV),
            "startTime": self.startTime and str(self.startTime),
            "lastRan": self.lastRan and str(self.lastRan)
        }

    @classmethod
    def loadFile(cls, bot, filename):
        """Load all change tasks from a file"""
        try:
            with open(filename, "r") as f:
                changesJson = json.load(f)
        except FileNotFoundError:
            changesJson = []
        for changeJson in changesJson:
            Change.load(bot, **changeJson)

    @classmethod
    def saveFile(cls, filename):
        """Save all change tasks to a file"""
        changesJson = [c.toJson() for c in cls.changes.values()]
        with open(filename, "w") as f:
            json.dump(changesJson, f)


class ChangeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.changeTask.start()

    def cog_unload(self):
        self.changeTask.cancel()

    @commandsplus.command(
        usage = "<x,-,/,+> <amount>"
    )
    @commands.guild_only()
    async def change(self, ctx, style, *, amount):
        """Change height"""
        digisize.changeUser(ctx.message.author.id, style, amount)
        userdata = userdb.load(ctx.message.author.id)
        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) changed {style}-style {amount}.")
        await ctx.send(f"User <@{ctx.message.author.id}> is now {userdata.height:m} ({userdata.height:u}) tall.")

    @commandsplus.command(
        hidden = True
    )
    @commands.check(requireAdmin)
    async def changes(self, ctx):
        await ctx.message.delete(delay=0)
        changeDump = "\n".join(str(c) for c in Change.changes.values())
        if not changeDump:
            changeDump = "No changes"
        await ctx.message.author.send("**CHANGES**\n" + changeDump)
        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) dumped the running changes.")

    @commandsplus.command(
        usage = "<rate>"
    )
    @commands.guild_only()
    async def slowchange(self, ctx, *, rateStr: str):
        addPerSec, mulPerSec, stopSV, stopTV = Rate.parse(rateStr)
        Change.start(self.bot, ctx.message.author.id, ctx.message.guild.id, addPerSec=addPerSec, mulPerSec=mulPerSec, stopSV=stopSV, stopTV=stopTV)
        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) slow-changed {addPerSec}/sec and *{mulPerSec}/sec until {stopSV} for {stopTV} seconds.")

    @commandsplus.command()
    @commands.guild_only()
    async def stopchange(self, ctx):
        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) stopped slow-changing.")

        deleted = Change.stop(ctx.message.author.id, ctx.message.guild.id)

        if deleted is None:
            await ctx.send("You can't stop slow-changing, as you don't have a task active!")
            await logger.warn(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) tried to stop slow-changing, but there didn't have a task active.")

    @commandsplus.command()
    @commands.guild_only()
    async def eatme(self, ctx):
        """Eat me!"""
        randmult = round(random.random(2, 20), 1)
        digisize.changeUser(ctx.message.author.id, "multiply", randmult)
        userdata = userdb.load(ctx.message.author.id)
        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) ate a cake and multiplied {randmult}.")
        # TODO: Randomize the italics message here
        await ctx.send(
            f"<@{ctx.message.author.id}> ate a :cake:! *I mean it said \"Eat me...\"*\n"
            f"They multiplied {randmult}x and are now {userdata.height:m} tall. ({userdata.height:u})")

    @commandsplus.command()
    @commands.guild_only()
    async def drinkme(self, ctx):
        """Drink me!"""
        userdata = userdb.load(ctx.message.author.id)
        randmult = round(random.random(2, 20), 1)
        digisize.changeUser(ctx.message.author.id, "divide", randmult)
        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) drank a potion and shrunk {randmult}.")
        # TODO: Randomize the italics message here
        await ctx.send(
            f"<@{ctx.message.author.id}> ate a :milk:! *I mean it said \"Drink me...\"*\n"
            f"They shrunk {randmult}x and are now {userdata.height:m} tall. ({userdata.height:u})")

    @tasks.loop(seconds=6)
    async def changeTask(self):
        """Slow growth task"""
        runningChanges = {}
        for key, change in Change.changes.items():
            try:
                running = await change.apply()
                if running:
                    runningChanges[key] = change
            except Exception as e:
                await logger.error(e)
        Change.changes = runningChanges
        Change.saveFile(conf.changespath)


def setup(bot):
    Change.loadFile(bot, conf.changespath)
    bot.add_cog(ChangeCog(bot))
