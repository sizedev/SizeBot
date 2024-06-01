from __future__ import annotations
from typing import Any

import json
import logging
from datetime import datetime
from dateutil.tz import tzlocal

import discord
from discord import Embed
from discord.ext import commands

from sizebot import __version__
from sizebot.lib import paths
from sizebot.lib.loglevels import EGG
from sizebot.lib.types import BotContext, GuildContext

logger = logging.getLogger("sizebot")


class ThisTracker():
    def __init__(self, points: dict[str, int] | None = None):
        if points is None:
            points = {}
        # Convert keys to integers
        intpoints = {int(k): v for k, v in points.items()}
        self.points = intpoints

    def increment_points(self, id: int):
        count = self.points.get(id, 0)
        self.points[id] = count + 1

    def save(self):
        paths.thispath.parent.mkdir(exist_ok = True)
        jsondata = self.toJSON()
        with open(paths.thispath, "w") as f:
            json.dump(jsondata, f, indent = 4)

    def toJSON(self) -> Any:
        """Return a python dictionary for json exporting"""
        return {
            "points": self.points,
        }

    @classmethod
    def load(cls) -> ThisTracker:
        try:
            with open(paths.thispath, "r") as f:
                jsondata = json.load(f)
        except FileNotFoundError:
            return ThisTracker()
        return ThisTracker.fromJSON(jsondata)

    @classmethod
    def fromJSON(cls, jsondata: Any) -> ThisTracker:
        points = jsondata["points"]
        return ThisTracker(points)


def is_agreement_emoji(emoji: str) -> bool:
    unicodeagreements = ["🔼", "⬆️", "⤴️", "☝️", "👆"]
    if isinstance(emoji, (discord.Emoji, discord.PartialEmoji)):
        if "this" in emoji.name.lower():
            return True
    else:
        if emoji in unicodeagreements:
            return True
    return False


def is_agreement_message(message: str) -> bool:
    textagreements = ["this", "^", "agree"]
    return is_agreement_emoji(message) or message.lower() in textagreements or message.startswith("^")


def find_latest_non_this(messages: list[discord.Message]) -> discord.Message:
    for message in messages:
        if not is_agreement_message(message.content):
            return message


class ThisCog(commands.Cog):
    """This Points!"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        aliases = ["points", "board"],
        hidden = True,
        category = "misc"
    )
    @commands.guild_only()
    async def leaderboard(self, ctx: GuildContext):
        """See who's the most agreeable!"""
        logger.log(EGG, f"{ctx.message.author.display_name} found the leaderboard!")
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
    async def on_message(self, m: discord.Message):
        if m.author.bot:
            return
        if is_agreement_message(m.content):
            channel = m.channel
            messages = [m async for m in channel.history(limit=100)]
            if find_latest_non_this(messages).author.id == m.author.id:
                return
            tracker = ThisTracker.load()
            tracker.increment_points(find_latest_non_this(messages).author.id)
            tracker.save()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, reacter: discord.Member | discord.User):
        if reaction.message.author.bot:
            return
        if reaction.message.author.id == reacter.id:
            return
        if is_agreement_emoji(reaction.emoji):
            tracker = ThisTracker.load()
            tracker.increment_points(reaction.message.author.id)
            tracker.save()


async def setup(bot: commands.Bot):
    await bot.add_cog(ThisCog(bot))
