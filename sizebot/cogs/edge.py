# The "edge" cog allows and  guild owners to set a largest/smallest user for their server.
# It does this by seeing if they are the largest or smallest user in the guild, and if they aren't setting their height
# to either 1.1x or 0.9x of the largest or smallest user in the guild, respectively.
from typing import Any

import logging
from sizebot.lib.errors import GuildNotFoundException, UserNotFoundException

import discord
from discord.ext import commands

from sizebot.lib import guilddb, userdb, nickmanager
from sizebot.lib.checks import is_mod
from sizebot.lib.types import GuildContext
from sizebot.lib.units import SV, Decimal

logger = logging.getLogger("sizebot")


# TODO: CamelCase
def getUserSizes(g: discord.Guild) -> Any:
    # Find the largest and smallest current users.
    # TODO: Can this be faster?
    # Like, if you sorted the users by size, would that make this faster?
    # It's 1:30AM and I don't want to check.
    smallestuser = None
    smallestsize = SV("infinity")
    largestuser = None
    largestsize = SV(0)
    allusers = {}
    for _, userid in userdb.list_users(guildid=g.id):
        member = g.get_member(userid)
        if not (member and str(member.status) != "offline"):
            continue
        userdata = userdb.load(g.id, userid)
        if userdata.height == 0 or userdata.height == SV("infinity"):
            continue
        if not userdata.is_active:
            continue
        if userdata.height > largestsize:
            largestuser = userid
            largestsize = userdata.height
        if userdata.height < smallestsize:
            smallestuser = userid
            smallestsize = userdata.height
        allusers[userid] = userdata.height
    return {"smallest": {"id": smallestuser, "size": smallestsize},
            "largest": {"id": largestuser, "size": largestsize},
            "users": allusers}


class EdgeCog(commands.Cog):
    """Commands to create or clear edge users."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        category = "mod",
        hidden = True
    )
    @is_mod()
    @commands.guild_only()
    async def edges(self, ctx: GuildContext):
        """See who is set to be the smallest and largest users."""
        guilddata = guilddb.load_or_create(ctx.guild.id)
        await ctx.send(f"**SERVER-SET SMALLEST AND LARGEST USERS:**\nSmallest: {'*Unset*' if guilddata.small_edge is None else guilddata.small_edge}\nLargest: {'*Unset*' if guilddata.large_edge is None else guilddata.large_edge}")

    @commands.command(
        aliases = ["smallest"],
        usage = "[user]",
        hidden = True,
        category = "mod"
    )
    @is_mod()
    @commands.guild_only()
    async def setsmallest(self, ctx: GuildContext, *, member: discord.Member):
        """Set the smallest user."""
        guilddata = guilddb.load_or_create(ctx.guild.id)
        guilddata.small_edge = member.id
        guilddb.save(guilddata)
        await ctx.send(f"<@{member.id}> is now the smallest user. They will be automatically adjusted to be the smallest user until they are removed from this role.")
        logger.info(f"{member.name} ({member.id}) is now the smallest user in guild {ctx.guild.id}.")

    @commands.command(
        aliases = ["largest"],
        usage = "[user]",
        hidden = True,
        category = "mod"
    )
    @is_mod()
    @commands.guild_only()
    async def setlargest(self, ctx: GuildContext, *, member: discord.Member):
        """Set the largest user."""
        guilddata = guilddb.load_or_create(ctx.guild.id)
        guilddata.large_edge = member.id
        guilddb.save(guilddata)
        await ctx.send(f"<@{member.id}> is now the largest user. They will be automatically adjusted to be the largest user until they are removed from this role.")
        logger.info(f"{member.name} ({member.id}) is now the largest user in guild {ctx.guild.id}.")

    @commands.command(
        aliases = ["resetsmallest", "removesmallest"],
        hidden = True,
        category = "mod"
    )
    @is_mod()
    @commands.guild_only()
    async def clearsmallest(self, ctx: GuildContext):
        """Clear the role of 'smallest user.'"""
        guilddata = guilddb.load_or_create(ctx.guild.id)
        guilddata.small_edge = None
        guilddb.save(guilddata)
        await ctx.send("Smallest user unset.")
        logger.info(f"Smallest user unset in guild {ctx.guild.id}.")

    @commands.command(
        aliases = ["resetlargest", "removelargest"],
        hidden = True,
        category = "mod"
    )
    @is_mod()
    @commands.guild_only()
    async def clearlargest(self, ctx: GuildContext):
        """Clear the role of 'largest user.'"""
        guilddata = guilddb.load_or_create(ctx.guild.id)
        guilddata.large_edge = None
        guilddb.save(guilddata)
        await ctx.send("Largest user unset.")
        logger.info(f"Largest user unset in guild {ctx.guild.id}.")

    @commands.command(
        hidden = True,
        category = "mod"
    )
    @is_mod()
    @commands.guild_only()
    async def edgedebug(self, ctx: GuildContext):
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        usersizes = getUserSizes(ctx.guild)
        guilddata = guilddb.load(ctx.guild.id)
        sm = guilddata.small_edge
        lg = guilddata.large_edge

        outstring = f"**CURRENT USER:**\nID: `{ctx.author.id}`\nHeight: `{userdata.height}`\n\n"
        outstring += f"**EDGES:**\nSmallest: {sm}\nLargest: {lg}\n\n"
        outstring += f"**SMALLEST USER:**\nID: `{usersizes['smallest']['id']}`\nHeight: `{usersizes['smallest']['size']}`\n\n"
        outstring += f"**LARGEST USER:**\nID: `{usersizes['largest']['id']}`\nHeight: `{usersizes['largest']['size']}`\n\n"
        outstring += "**ALL USERS:**\n"

        for pair in usersizes['users'].items():
            outstring += f"`{pair[0]}`: {pair[1]}\n"

        await ctx.send(outstring)

    @commands.Cog.listener()
    async def on_message(self, m: discord.Message):
        # non-guild messages
        if m.guild is None or not isinstance(m.author, discord.Member):
            return

        try:
            guilddata = guilddb.load(m.guild.id)
        except GuildNotFoundException:
            return  # Guild does not have edges set

        sm = guilddata.small_edge
        lg = guilddata.large_edge
        if not (m.author.id == sm or m.author.id == lg):
            return  # The user is not set to be the smallest or the largest user.

        try:
            userdata = userdb.load(m.guild.id, m.author.id)
        except UserNotFoundException:
            return

        usersizes = getUserSizes(m.guild)
        smallestuser = usersizes["smallest"]["id"]
        smallestsize = usersizes["smallest"]["size"]
        largestuser = usersizes["largest"]["id"]
        largestsize = usersizes["largest"]["size"]

        if sm == m.author.id:
            if m.author.id == smallestuser:
                return
            elif userdata.height == SV(0):
                return
            else:
                userdata.height = smallestsize * Decimal(0.9)
                userdb.save(userdata)

        if lg == m.author.id:
            if m.author.id == largestuser:
                return
            elif userdata.height == SV("infinity"):
                return
            else:
                userdata.height = largestsize * Decimal(1.1)
                userdb.save(userdata)

        if userdata.display:
            await nickmanager.nick_update(m.author)


async def setup(bot: commands.Bot):
    await bot.add_cog(EdgeCog(bot))
