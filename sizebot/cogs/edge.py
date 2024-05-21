# The "edge" cog allows and  guild owners to set a largest/smallest user for their server.
# It does this by seeing if they are the largest or smallest user in the guild, and if they aren't setting their height
# to either 1.1x or 0.9x of the largest or smallest user in the guild, respectively.
from collections.abc import Iterable

import logging
from dataclasses import dataclass

import discord
from discord.ext import commands

from sizebot.lib.errors import GuildNotFoundException, UserNotFoundException
from sizebot.lib import guilddb, userdb, nickmanager
from sizebot.lib.checks import is_mod
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.types import BotContext
from sizebot.lib.units import SV

logger = logging.getLogger("sizebot")


@dataclass
class UserSize:
    id: int | None
    size: SV


@dataclass
class UserSizes:
    smallest: UserSize
    largest: UserSize
    users: list[UserSize]


def _get_active_users(guild: discord.Guild) -> Iterable[UserSize]:
    for guildid, userid in userdb.list_users(guildid=guild.id):
        member = guild.get_member(userid)
        if member is None or str(member.status) == "offline":
            continue
        userdata = userdb.load(guildid, userid)
        if userdata.height == 0 or userdata.height == SV.infinity:
            continue
        if not userdata.is_active:
            continue
        yield UserSize(userid, userdata.height)


def _get_user_sizes(g: discord.Guild) -> UserSizes:
    # Find the largest and smallest current users.
    # TODO: Can this be faster?
    # Like, if you sorted the users by size, would that make this faster?
    # It's 1:30AM and I don't want to check.
    smallest = UserSize(None, SV.infinity)
    largest = UserSize(None, SV(0))
    users: list[UserSize] = []
    for user in _get_active_users(g):
        if user.size > largest.size:
            largest = user
        if user.size < smallest.size:
            smallest = user
        users.append(user)
    return UserSizes(smallest, largest, users)


class EdgeCog(commands.Cog):
    """Commands to create or clear edge users."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        category = "mod",
        hidden = True
    )
    @is_mod()
    async def edges(self, ctx: BotContext):
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
    async def setsmallest(self, ctx: BotContext, *, member: discord.Member):
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
    async def setlargest(self, ctx: BotContext, *, member: discord.Member):
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
    async def clearsmallest(self, ctx: BotContext):
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
    async def clearlargest(self, ctx: BotContext):
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
    async def edgedebug(self, ctx: BotContext):
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        usersizes = _get_user_sizes(ctx.guild)
        guilddata = guilddb.load(ctx.guild.id)
        sm = guilddata.small_edge
        lg = guilddata.large_edge

        outstring = f"**CURRENT USER:**\nID: `{ctx.author.id}`\nHeight: `{userdata.height}`\n\n"
        outstring += f"**EDGES:**\nSmallest: {sm}\nLargest: {lg}\n\n"
        outstring += f"**SMALLEST USER:**\nID: `{usersizes.smallest.id}`\nHeight: `{usersizes.smallest.size}`\n\n"
        outstring += f"**LARGEST USER:**\nID: `{usersizes.largest.id}`\nHeight: `{usersizes.largest.size}`\n\n"
        outstring += "**ALL USERS:**\n"

        for u in usersizes.users:
            outstring += f"`{u.id}`: {u.size}\n"

        await ctx.send(outstring)

    @commands.Cog.listener()
    async def on_message(self, m: discord.Message):
        # non-guild messages
        if not isinstance(m.author, discord.Member):
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

        usersizes = _get_user_sizes(m.guild)

        if sm == m.author.id:
            if m.author.id == usersizes.smallest.id:
                return
            if userdata.height == SV(0):
                return
            userdata.height = usersizes.smallest.size * Decimal(0.9)
            userdb.save(userdata)

        if lg == m.author.id:
            if m.author.id == usersizes.largest.id:
                return
            if userdata.height == SV.infinity:
                return
            userdata.height = usersizes.largest.size * Decimal(1.1)
            userdb.save(userdata)

        if userdata.display:
            await nickmanager.nick_update(m.author)


async def setup(bot: commands.Bot):
    await bot.add_cog(EdgeCog(bot))
