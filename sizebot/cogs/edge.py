# The "edge" extensions allows bot admins (and later guild owners [SB4]) to set a largest/smallest user (for their server [SB4]).
# It does this by sseeing if they are the largest or smallest user (in the guild [SB4]), and if they aren't setting their height
# to either 1.1x or 0.9x of the largest or smallest user (in the guild [SB4]), respectively.

import toml
import logging
from os import listdir

import discord
from discord.ext import commands
from sizebot.discordplus import commandsplus

import sizebot.lib.decimal as Decimal
from sizebot import conf
from sizebot.lib import userdb
from sizebot.lib import proportions
from sizebot.lib.units import SV

logger = logging.getLogger("sizebot")

# Read the edges file.
try:
    with open(conf.edgepath, "r") as f:
        edgedict = toml.loads(f.read())
except (FileNotFoundError, TypeError, toml.TomlDecodeError):
    edgedict = {"edges": {"smallest": None, "largest": None}}
    with open(conf.edgepath, "w") as f:
        f.write(toml.dump(edgedict))


async def on_message(m):
    if m.author.id != edgedict.get("smallest", None) or m.author.id != edgedict.get("largest", None):
        return  # The user is not set to be the smallest or the largest user.

    userdata = userdb.load(m.author.id)

    # Find the largest and smallest current users.
    smallestuser = 000000000000000000
    smallestsize = SV(SV.infinity)
    largestuser = 000000000000000000
    largestsize = SV(0)
    userfilelist = listdir(conf.userdbpath)
    for userfile in userfilelist:
        testid = userfile[:-5]  # Remove the ".json" from the file name, leaving us with the ID.
        testdata = userdb.load(testid)
        if testdata.height <= 0 or testdata.height >= SV.infinity:
            break
        if testdata.height > largestsize:
            largestuser = testid
            largestsize = testdata.height
        if testdata.height < smallestsize:
            smallestuser = testid
            smallestsize = testdata.height

    if edgedict.get("smallest", None) == m.author.id:
        if m.author.id == smallestuser:
            return
        elif userdata.height == SV(0):
            return
        else:
            userdata.height = smallestsize * Decimal(0.9)
            userdb.save(userdata)
            logger.info(f"User {m.author.id} ({m.author.display_name}) is now {userdata.height:m} tall, so that they stay the smallest.")

    if edgedict.get("largest", None) == m.author.id:
        if m.author.id == largestuser:
            return
        elif userdata.height == SV(SV.infinity):
            return
        else:
            userdata.height = largestsize * Decimal(1.1)
            userdb.save(userdata)
            logger.info(f"User {m.author.id} ({m.author.display_name}) is now {userdata.height:m} tall, so that they stay the largest.")

    if userdata.display:
        await proportions.nickUpdate(m.author)


class EdgeCog(commands.Cog):
    """Commands to create or clear edge users."""

    def __init__(self, bot):
        self.bot = bot

    @commandsplus.command(
        aliases = ["smallest"],
        usage = "[user]"
    )
    @commands.is_owner()
    async def setsmallest(self, ctx, *, member: discord.Member):
        edgedict["smallest"] = member.id
        with open(conf.edgepath, "w") as f:
            f.write(toml.dump(edgedict))

    @commandsplus.command(
        aliases = ["largest"],
        usage = "[user]"
    )
    @commands.is_owner()
    async def setlargest(self, ctx, *, member: discord.Member):
        edgedict["largest"] = member.id
        with open(conf.edgepath, "w") as f:
            f.write(toml.dump(edgedict))

    @commandsplus.command(
        aliases = ["resetsmallest", "removesmallest"],
        usage = "[user]"
    )
    @commands.is_owner()
    async def clearsmallest(self, ctx, *, member: discord.Member):
        edgedict["smallest"] = None
        with open(conf.edgepath, "w") as f:
            f.write(toml.dump(edgedict))

    @commandsplus.command(
        aliases = ["resetlargest", "removelargest"],
        usage = "[user]"
    )
    @commands.is_owner()
    async def clearlargest(self, ctx, *, member: discord.Member):
        edgedict["largest"] = None
        with open(conf.edgepath, "w") as f:
            f.write(toml.dump(edgedict))
