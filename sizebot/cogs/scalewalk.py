import logging

import discord
from sizebot.lib import proportions
from sizebot.lib import userdb

from discord.ext import commands

from sizebot.lib.decimal import Decimal
from sizebot.lib.diff import Diff
from sizebot.lib.errors import DigiContextException
from sizebot.lib.units import SV

logger = logging.getLogger("sizebot")


def steps(start_inc: SV, diff: Diff, goal: SV):
    """Return the number of steps it would take to reach `goal` from 0,
    first by increasing by `start_inc`, then by `start_inc` * `mult`,
    repeating this process until `goal` is reached.

    Returns (steps, final increment, start inc. / final inc.)"""

    steps = 0
    current_pos = 0
    last_pos = None
    current_inc = start_inc

    while not current_pos >= goal:
        steps += 1
        last_pos = current_pos
        current_pos += current_inc
        if current_pos >= goal:
            return (Decimal(steps), current_inc, start_inc / current_inc)
        if current_pos == last_pos:
            return (Decimal("inf"), SV(0), Decimal("inf"))
        if diff.changetype == "add":
            current_inc += diff.amount
        elif diff.changetype == "multiply":
            current_inc *= diff.amount
        else:
            raise DigiContextException("This change type is not yet supported for scale-walking.")


class ScaleWalkCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        category = "stats",
        usage = "<change per step> <distance> [apply]"
    )
    async def scalewalk(self, ctx, change: Diff, dist: SV, flag = None):
        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)
        stats = proportions.PersonStats(userdata)

        stepcount, final_inc, final_ratio = steps(stats.walksteplength, change, dist)

        finalheight = SV(userdata.height / final_ratio)

        symbol = ""
        if change.changetype == "add":
            symbol = "+"
        if change.changetype == "multiply":
            symbol = "x"

        amountstring = ""
        if change.changetype == "add":
            amountstring = f"{symbol}{change.amount:,.3mu}"
        if change.changetype == "multiply":
            amountstring = f"{symbol}{change.amount:,.3}"

        if flag is None:
            e = discord.Embed(
                title = f"If {userdata.nickname} walked {dist:,.3mu}, scaling {amountstring} each step...",
                description = f"They would now be **{finalheight:,.3mu}** tall after **{stepcount}** steps."
            )
            await ctx.send(embed = e)
        elif flag == "apply":
            userdata.height = finalheight
            userdb.save(userdata)

            e = discord.Embed(
                title = f"{userdata.nickname} walked {dist:,.3mu}, scaling {amountstring} each step...",
                description = f"They are now **{finalheight:,.3mu}** tall after **{stepcount}** steps."
            )
            await ctx.send(embed = e)
        else:
            raise DigiContextException(f"Invalid flag {flag}.")

    @commands.command(
        category = "stats",
        usage = "<change per step> <distance> [apply]"
    )
    async def scalerun(self, ctx, change: Diff, dist: SV, flag = None):
        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)
        stats = proportions.PersonStats(userdata)

        stepcount, final_inc, final_ratio = steps(stats.runsteplength, change, dist)

        finalheight = SV(userdb.height / final_ratio)

        symbol = ""
        if change.changetype == "add":
            symbol = "+"
        if change.changetype == "multiply":
            symbol = "x"

        amountstring = ""
        if change.changetype == "add":
            amountstring = f"{symbol}{change.amount:,.3mu}"
        if change.changetype == "multiply":
            amountstring = f"{symbol}{change.amount:,.3}"

        if flag is None:
            e = discord.Embed(
                title = f"If {userdata.nickname} ran {dist:,.3mu}, scaling {amountstring} each step...",
                description = f"They would now be **{finalheight:,.3mu}** tall after **{stepcount}** steps."
            )
            await ctx.send(embed = e)
        elif flag == "apply":
            userdata.height = finalheight
            userdb.save(userdata)

            e = discord.Embed(
                title = f"{userdata.nickname} ran {dist:,.3mu}, scaling {amountstring} each step...",
                description = f"They are now **{finalheight:,.3mu}** tall after **{stepcount}** steps."
            )
            await ctx.send(embed = e)
        else:
            raise DigiContextException(f"Invalid flag {flag}.")


def setup(bot):
    bot.add_cog(ScaleWalkCog(bot))
