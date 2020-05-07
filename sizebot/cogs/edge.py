# The "edge" cog allows bot admins (and later guild owners [SB4]) to set a largest/smallest user (for their server [SB4]).
# It does this by seeing if they are the largest or smallest user (in the guild [SB4]), and if they aren't setting their height
# to either 1.1x or 0.9x of the largest or smallest user (in the guild [SB4]), respectively.

import logging

import toml

import discord
from discord.ext import commands

from sizebot import conf
from sizebot.discordplus import commandsplus
from sizebot.lib import proportions
from sizebot.lib import userdb
from sizebot.lib.checks import is_mod
from sizebot.lib.decimal import Decimal
from sizebot.lib.units import SV

logger = logging.getLogger("sizebot")


# Read the edges file.
def getEdgesFile(gid):
    edgepath = conf.guilddbpath / str(gid) / "edges.ini"

    try:
        with open(edgepath, "r") as f:
            edgedict = toml.loads(f.read())
    except (FileNotFoundError, TypeError, toml.TomlDecodeError):
        edgedict = {"edges": {"smallest": None, "largest": None}}
        edgepath.parent.mkdir(parents = True, exist_ok = True)
        with open(edgepath, "w") as f:
            f.write(toml.dumps(edgedict))

    return edgedict


def getUserSizes(g):
    # Find the largest and smallest current users.
    # TODO: Check to see if these users are recently active, which would determine if they count towards the check.
    smallestuser = 000000000000000000
    smallestsize = SV(SV.infinity)
    largestuser = 000000000000000000
    largestsize = SV(0)
    allusers = {}
    for _, testid in userdb.listUsers(g.id):
        if testid in list([m.id for m in g.members if str(m.status) != "offline"]):
            testdata = userdb.load(g.id, testid)
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
    # non-guild messages
    if not isinstance(m.author, discord.Member):
        return

    edgedict = getEdgesFile(m.guild.id)
    sm = edgedict.get("smallest", None)
    lg = edgedict.get("largest", None)
    if m.author.id != sm and m.author.id != lg:
        return  # The user is not set to be the smallest or the largest user.

    userdata = userdb.load(m.guild.id, m.author.id)

    usersizes = getUserSizes(m.guild)
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

    @commandsplus.command(
        category = "misc"
    )
    async def edges(self, ctx):
        """See who is set to be the smallest and largest users."""
        edgedict = getEdgesFile(ctx.guild.id)
        await ctx.send(f"**SERVER-SET SMALLEST AND LARGEST USERS:**\nSmallest: {edgedict.get('smallest', '*Unset*')}\nLargest: {edgedict.get('largest', '*Unset*')}")

    @commandsplus.command(
        aliases = ["smallest"],
        usage = "[user]",
        hidden = True,
        category = "mod"
    )
    @is_mod()
    async def setsmallest(self, ctx, *, member: discord.Member):
        """Set the smallest user."""
        edgedict = getEdgesFile(ctx.guild.id)
        edgedict["smallest"] = member.id
        with open(conf.edgepath, "w") as f:
            f.write(toml.dumps(edgedict))
        await ctx.send(f"<@{member.id}> is now the smallest user. They will be automatically adjusted to be the smallest user until they are removed from this role.")
        logger.info(f"{member.name} ({member.id}) is now the smallest user.")

    @commandsplus.command(
        aliases = ["largest"],
        usage = "[user]",
        hidden = True,
        category = "mod"
    )
    @is_mod()
    async def setlargest(self, ctx, *, member: discord.Member):
        """Set the largest user."""
        edgedict = getEdgesFile(ctx.guild.id)
        edgedict["largest"] = member.id
        with open(conf.edgepath, "w") as f:
            f.write(toml.dumps(edgedict))
        await ctx.send(f"<@{member.id}> is now the largest user. They will be automatically adjusted to be the largest user until they are removed from this role.")
        logger.info(f"{member.name} ({member.id}) is now the largest user.")

    @commandsplus.command(
        aliases = ["resetsmallest", "removesmallest"],
        hidden = True,
        category = "mod"
    )
    @is_mod()
    async def clearsmallest(self, ctx):
        """Clear the role of 'smallest user.'"""
        edgedict = getEdgesFile(ctx.guild.id)
        edgedict["smallest"] = None
        with open(conf.edgepath, "w") as f:
            f.write(toml.dumps(edgedict))
        await ctx.send("Smallest user unset.")
        logger.info("Smallest user unset.")

    @commandsplus.command(
        aliases = ["resetlargest", "removelargest"],
        hidden = True,
        category = "mod"
    )
    @is_mod()
    async def clearlargest(self, ctx):
        """Clear the role of 'largest user.'"""
        edgedict = getEdgesFile(ctx.guild.id)
        edgedict["largest"] = None
        with open(conf.edgepath, "w") as f:
            f.write(toml.dumps(edgedict))
        await ctx.send("Largest user unset.")
        logger.info("Largest user unset.")

    @commandsplus.command(
        hidden = True,
        category = "mod"
    )
    @is_mod()
    async def edgedebug(self, ctx):
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        usersizes = getUserSizes(ctx.guild)
        edgedict = getEdgesFile(ctx.guild.id)
        sm = edgedict.get("smallest", None)
        lg = edgedict.get("largest", None)

        outstring = f"**CURRENT USER:**\nID: `{ctx.author.id}`\nHeight: `{userdata.height}`\n\n"
        outstring += f"**EDGES:**\nSmallest: {sm}\nLargest: {lg}\n\n"
        outstring += f"**SMALLEST USER:**\nID: `{usersizes['smallest']['id']}`\nHeight: `{usersizes['smallest']['size']}`\n\n"
        outstring += f"**LARGEST USER:**\nID: `{usersizes['largest']['id']}`\nHeight: `{usersizes['largest']['size']}`\n\n"
        outstring += "**ALL USERS:**\n"

        for pair in usersizes['users'].items():
            outstring += f"`{pair[0]}`: {pair[1]}\n"

        await ctx.send(outstring)


def setup(bot):
    bot.add_cog(EdgeCog(bot))
