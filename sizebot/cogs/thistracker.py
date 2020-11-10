import json
from datetime import datetime
from dateutil.tz import tzlocal

import discord
from discord import Embed
from discord.ext import commands

from sizebot import __version__
from sizebot.lib import paths


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
        paths.thispath.parent.mkdir(exist_ok = True)
        jsondata = self.toJSON()
        with open(paths.thispath, "w") as f:
            json.dump(jsondata, f, indent = 4)

    def toJSON(self):
        """Return a python dictionary for json exporting"""
        return {
            "points": self.points,
        }

    @classmethod
    def load(cls):
        try:
            with open(paths.thispath, "r") as f:
                jsondata = json.load(f)
        except FileNotFoundError:
            return ThisTracker()
        return ThisTracker.fromJSON(jsondata)

    @classmethod
    def fromJSON(cls, jsondata):
        points = jsondata["points"]
        return ThisTracker(points)


def isAgreementEmoji(emoji):
    unicodeagreements = ["🔼", "⬆️", "⤴️", "☝️", "👆"]
    if isinstance(emoji, (discord.Emoji, discord.PartialEmoji)):
        if "this" in emoji.name.lower():
            return True
    else:
        if emoji in unicodeagreements:
            return True


def isAgreementMessage(message):
    textagreements = ["this", "^", "agree"]
    return isAgreementEmoji(message) or message.lower() in textagreements or message.startswith("^")


def findLatestNonThis(messages):
    for message in messages:
        if not isAgreementMessage(message.content):
            return message


class ThisCog(commands.Cog):
    """This Points!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases = ["points", "board"],
        hidden = True,
        category = "misc"
    )
    @commands.guild_only()
    async def leaderboard(self, ctx):
        """See who's the most agreeable!"""
        now = datetime.now(tzlocal())
        tracker = ThisTracker.load()
        trackerlist = sorted(tracker.points.items(), key=lambda i: i[1], reverse= True)
        embed = Embed(title="The Most Agreeable Users", color=0x31eff9)
        embed.set_author(name=f"SizeBot {__version__}")
        messagetosend = ""
        totalpoints = sum(tracker.points.values())
        for userid, points in trackerlist[0:10]:
            messagetosend += f"**{self.bot.get_user(userid).display_name}**: {points}\n"
        embed.add_field(name=f"{totalpoints} total agreements", value=messagetosend.strip(), inline=False)
        embed.set_footer(text=f"{now.strftime('%d %b %Y %H:%M:%S %Z')}")
        await ctx.send(embed = embed)

    @commands.Cog.listener()
    async def on_message(self, m):
        if m.author.bot:
            return
        if isAgreementMessage(m.content):
            channel = m.channel
            messages = await channel.history(limit=100).flatten()
            if findLatestNonThis(messages).author.id == m.author.id:
                return
            tracker = ThisTracker.load()
            tracker.incrementPoints(findLatestNonThis(messages).author.id)
            tracker.save()

    @commands.Cog.listener()
    async def on_reaction_add(self, r, u):
        if r.message.author.bot:
            return
        if r.message.author.id == u.id:
            return
        if isAgreementEmoji(r.emoji):
            tracker = ThisTracker.load()
            tracker.incrementPoints(r.message.author.id)
            tracker.save()


def setup(bot):
    bot.add_cog(ThisCog(bot))
