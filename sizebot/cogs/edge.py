# The "edge" extensions allows bot admins (and later guild owners [SB4]) to set a largest/smallest user (for their server [SB4]).
# It does this by sseeing if they are the largest or smallest user (in the guild [SB4]), and if they aren't setting their height
# to either 1.1x or 0.9x of the largest or smallest user (in the guild [SB4]), respectively.

import toml
import logging
from os import listdir

import discord
from discord.ext import commands
from sizebot.discordplus import commandsplus

from sizebot import conf
from sizebot.lib import userdb
from sizebot.lib import proportions
from sizebot.lib.units import SV
from sizebot.lib.decimal import Decimal

logger = logging.getLogger("sizebot")

# Read the edges file.
try:
    with open(conf.edgepath, "r") as f:
        edgedict = toml.loads(f.read())
except (FileNotFoundError, TypeError, toml.TomlDecodeError):
    edgedict = {"edges": {"smallest": None, "largest": None}}
    with open(conf.edgepath, "w") as f:
        f.write(toml.dumps(edgedict))


def getUserSizes():
    # Find the largest and smallest current users.
    # TODO: Check to see if these users are recently active, which would determine if they count towards the check.
    smallestuser = 000000000000000000
    smallestsize = SV(SV.infinity)
    largestuser = 000000000000000000
    largestsize = SV(0)
    userfilelist = listdir(conf.userdbpath)
    allusers = {}
    for userfile in userfilelist:
        testid = userfile[:-5]  # Remove the ".json" from the file name, leaving us with the ID.
        testdata = userdb.load(testid)
        allusers[testid] = testdata.height
        if testdata.height <= 0 or testdata.height >= SV.infinity:
            break
        if testdata.height > largestsize:
            largestuser = testid
            largestsize = testdata.height
        if testdata.height < smallestsize:
            smallestuser = testid
            smallestsize = testdata.height

    smallestuser = int(smallestuser)
    largestuser = int(largestuser)

    return {"smallest": {"id": smallestuser, "size": smallestsize},
            "largest": {"id": largestuser, "size": largestsize},
            "users": allusers}


async def on_message(m):
    sm = edgedict.get("smallest", None)
    lg = edgedict.get("largest", None)
    if m.author.id != sm and m.author.id != lg:
        return  # The user is not set to be the smallest or the largest user.

    userdata = userdb.load(m.author.id)

    usersizes = getUserSizes()
    smallestuser = usersizes["smallest"]["id"]
    smallestsize = usersizes["smallest"]["size"]
    largestuser = usersizes["largest"]["id"]
    largestsize = usersizes["largest"]["size"]

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

    @commandsplus.command()
    async def edges(self, ctx):
        """See who is set to be the smallest and largest users."""
        await ctx.send(f"**SERVER-SET SMALLEST AND LARGEST USERS:**\nSmallest: {edgedict.get('smallest', '*Unset*')}\nLargest: {edgedict.get('largest', '*Unset*')}")

    @commandsplus.command(
        aliases = ["smallest"],
        usage = "[user]"
    )
    @commands.is_owner()
    async def setsmallest(self, ctx, *, member: discord.Member):
        """Set the smallest user."""
        edgedict["smallest"] = member.id
        with open(conf.edgepath, "w") as f:
            f.write(toml.dumps(edgedict))
        await ctx.send(f"<@{member.id}> is now the smallest user. They will be automatically adjusted to be the smallest user until they are removed from this role.")
        logger.info(f"{member.name} ({member.id}) is now the smallest user.")

    @commandsplus.command(
        aliases = ["largest"],
        usage = "[user]"
    )
    @commands.is_owner()
    async def setlargest(self, ctx, *, member: discord.Member):
        """Set the largest user."""
        edgedict["largest"] = member.id
        with open(conf.edgepath, "w") as f:
            f.write(toml.dumps(edgedict))
        await ctx.send(f"<@{member.id}> is now the largest user. They will be automatically adjusted to be the largest user until they are removed from this role.")
        logger.info(f"{member.name} ({member.id}) is now the largest user.")

    @commandsplus.command(
        aliases = ["resetsmallest", "removesmallest"]
    )
    @commands.is_owner()
    async def clearsmallest(self, ctx):
        """Clear the role of 'smallest user.'"""
        edgedict["smallest"] = None
        with open(conf.edgepath, "w") as f:
            f.write(toml.dumps(edgedict))
        await ctx.send("Smallest user unset.")
        logger.info("Smallest user unset.")

    @commandsplus.command(
        aliases = ["resetlargest", "removelargest"]
    )
    @commands.is_owner()
    async def clearlargest(self, ctx):
        """Clear the role of 'largest user.'"""
        edgedict["largest"] = None
        with open(conf.edgepath, "w") as f:
            f.write(toml.dumps(edgedict))
        await ctx.send("Largest user unset.")
        logger.info("Largest user unset.")


def setup(bot):
    bot.add_cog(EdgeCog(bot))
