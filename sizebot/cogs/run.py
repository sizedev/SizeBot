from time import time

from discord.ext import commands, tasks
from sizebot.discordplus import commandsplus

from sizebot import logger
from sizebot.lib import utils
from sizebot.lib.units import TV
from sizebot.digidecimal import Decimal

runners = []


def buildNyan(progress):
    nyanTrail = "<a:nyanTrail:667175870711988254>"
    nyanCat = "<a:nyanEnd:667175883697684510>"
    maxRun = 33
    steps = utils.clamp(0, int(progress * maxRun), maxRun)
    return f"\u200b{steps * nyanTrail}{nyanCat}"


def buildRun(progress):
    maxRun = 167
    steps = utils.clamp(0, int(progress * maxRun), maxRun)
    remaining = maxRun - steps
    return f"\u200b🏁{remaining * ' '}🏃‍♀️"


class Runner:
    def __init__(self, channelId, messageId, *, startTime, duration, nyan=False):
        self.channelId = channelId
        self.messageId = messageId
        self.startTime = Decimal(startTime)
        self.duration = TV(duration)
        self.nyan = nyan
        self.now = Decimal(startTime)

    async def step(self, bot):
        self.now = Decimal(time())
        channel = bot.get_channel(self.channelId)
        message = await channel.fetch_message(self.messageId)
        await message.edit(content=self.formatRunner())
        running = self.running
        return running

    @property
    def progress(self):
        """Progress 0.0-1.0"""
        progress = utils.clamp(Decimal(0), (self.now - self.startTime) / self.duration, Decimal(1))
        return progress

    @property
    def running(self):
        running = self.progress <= Decimal(1)
        return running

    @property
    def endtime(self):
        endtime = self.startTime + self.duration
        return endtime

    def formatRunner(self):
        if self.nyan:
            formatted = buildNyan(self.progress)
        else:
            formatted = buildRun(self.progress)
        return formatted

    @classmethod
    def start(cls, channelId, messageId, *, duration, nyan):
        startTime = Decimal(time())
        runner = cls(channelId, messageId, startTime=startTime, duration=duration, nyan=nyan)
        runners.append(runner)


class RunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.runTask.start()

    def cog_unload(self):
        self.runTask.cancel()

    @commandsplus.command(
        hidden = True
    )
    async def run(self, ctx, duration: TV, mode: str = ""):
        nyan = mode == "nyan"
        msg = await ctx.send("Ready... Set... GO")
        Runner.start(ctx.channel.id, msg.id, duration=duration, nyan=nyan)

    @tasks.loop(seconds=1)
    async def runTask(self):
        global runners
        try:
            runners = [r for r in runners if await r.step(self.bot)]
        except Exception as e:
            await logger.error(e)


def setup(bot):
    bot.add_cog(RunCog(bot))
