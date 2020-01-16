from time import time

from discord.ext import commands, tasks
from sizebot.discordplus import commandsplus

from sizebot.utils import clamp
from sizebot.digiSV import TV
from sizebot.digidecimal import Decimal

runners = []


def buildNyan(progress):
    nyanTrail = "<a:nyanTrail:667175870711988254>"
    nyanCat = "<a:nyanEnd:667175883697684510>"
    maxRun = 102
    steps = clamp(0, int(progress * maxRun), maxRun)
    trails, spaces = divmod(steps, 6)
    return f"{spaces * ' '}{trails * nyanTrail}{nyanCat}"


def buildRun(progress):
    maxRun = 167
    steps = clamp(0, int(progress * maxRun), maxRun)
    remaining = maxRun - steps
    return f"🏁{remaining * ' '}🏃‍♀️"


class Runner:
    def __init__(self, channelId, messageId, *, startTime, duration, nyan=False):
        self.channelId = channelId
        self.messageId = messageId
        self.startTime = Decimal(startTime)
        self.duration = TV(duration)
        self.nyan = nyan

    async def step(self, bot):
        channel = bot.get_channel(self.channelId)
        message = await channel.fetch_message(self.messageId)
        await message.edit(self.formatRunner())
        return self.running

    @property
    def progress(self):
        """Progress 0.0-1.0"""
        now = Decimal(time.time())
        return max(Decimal(0), self.endtime - now) / self.duration

    @property
    def running(self):
        now = Decimal(time.time())
        return self.endtime >= now

    @property
    def endtime(self):
        return self.startTime + self.duration

    def formatRunner(self):
        if self.nyan:
            return buildNyan(self.progress)
        else:
            return buildRun(self.progress)

    @classmethod
    def start(cls, channelId, messageId, *, duration, nyan):
        startTime = Decimal(time.time())
        runner = cls(channelId, messageId, startTime=startTime, duration=duration, nyan=nyan)
        runners.append(runner)


class RunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commandsplus.command(
        hidden = True
    )
    async def run(self, ctx, duration: TV, mode: str = ""):
        nyan = mode == "nyan"
        Runner.start(ctx.channel.id, ctx.message.id, duration=duration, nyan=nyan)

    @tasks.loop(seconds=1)
    async def changeTask(self):
        global runners
        runners = [r for r in runners if r.run(self.bot)]


def setup(bot):
    bot.add_cog(RunCog(bot))
