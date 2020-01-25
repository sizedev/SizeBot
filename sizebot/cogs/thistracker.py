import json
import discord
from discord.ext import commands

from sizebot import conf


class ThisTracker():
    def __init__(self, points=None):
        if points is None:
            points = {}
        else:
            # Convert keys to integers
            points = {int(k): v for k, v in points.items()}
        self.points = points

    def incrementPoints(self, id):
        count = self.points.get(id, 0)
        self.points[id] = count + 1

    def save(self):
        conf.thispath.parent.mkdir(exist_ok = True)
        jsondata = self.toJSON()
        with open(conf.thispath, "w") as f:
            json.dump(jsondata, f, indent = 4)

    def toJSON(self):
        """Return a python dictionary for json exporting"""
        return {
            "points": self.points,
        }

    @classmethod
    def load(cls):
        try:
            with open(conf.thispath, "r") as f:
                jsondata = json.load(f)
        except FileNotFoundError:
            return ThisTracker()
        return ThisTracker.fromJSON(jsondata)

    @classmethod
    def fromJSON(cls, jsondata):
        points = jsondata["points"]
        return ThisTracker(points)


def findLatestNonThis(messages):
    for message in messages:
        if not message.content.startswith("^") or message.content.lower() in ["this", "🔼", "⬆️", "⤴️"]:
            return message


class ThisCog(commands.Cog):
    """This Points!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, m):
        if m.author.bot:
            return
        if m.content.startswith("^") or m.content.lower() == "this":
            channel = m.channel
            messages = await channel.history(limit=100).flatten()
            tracker = ThisTracker.load()
            tracker.incrementPoints(findLatestNonThis(messages).author.id)
            tracker.save()

    @commands.Cog.listener()
    async def on_reaction_add(self, r, u):
        tracker = ThisTracker.load()
        if r.message.author.bot:
            return
        if isinstance(r, discord.Reaction):
            if r.emoji.name.lower() in ["this", "brilliancethis", "braverythis", "balancethis", "123this"]:
                tracker.incrementPoints(r.message.author.id)
                tracker = ThisTracker.load()
        else:
            if r.emoji in ["🔼", "⬆️", "⤴️"]:
                tracker.incrementPoints(r.message.author.id)
                tracker.save()


def setup(bot):
    bot.add_cog(ThisCog(bot))
