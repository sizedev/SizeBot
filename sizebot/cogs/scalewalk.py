import math
import logging

import discord
from sizebot.lib import proportions
from sizebot.lib import userdb

from discord.ext import commands

from sizebot.lib.decimal import Decimal
from sizebot.lib.diff import Diff
from sizebot.lib.errors import ChangeMethodInvalidException, DigiContextException
from sizebot.lib.units import SV

logger = logging.getLogger("sizebot")


def get_steps(start_inc: SV, diff: Diff, goal: SV):
    """Return the number of steps it would take to reach `goal` from 0,
    first by increasing by `start_inc`, then by `start_inc` * `mult`,
    repeating this process until `goal` is reached.

    Returns (steps, final increment, start inc. / final inc.)"""

    if (diff.changetype == "add" and diff.amount == 0) or (diff.changetype == "multiply" and diff.amount == 1):
        # TODO: Handle special case of walking without size change
        if start_inc <= 0:
            return (Decimal("inf"), SV(0), Decimal("inf"))
        # Calculate number of steps required to reach goal
        steps = math.ceil(goal / start_inc)
        # Calculate how far user got after those steps
        # current_pos = start_inc * steps
        return (Decimal(steps), start_inc, 1)
    elif diff.changetype == "add":
        if diff.amount < 0:
            # Calculate max distance travelled, if each step is getting shorter
            max_dist = ((diff.amount / 2) - start_inc) / diff.amount
            if max_dist < goal:
                return (Decimal("inf"), SV(0), Decimal("inf"))
        # Calculate number of steps required to reach goal
        # https://www.wolframalpha.com/input/?i=g+%3D+%28s+*+t%29+%2B+%28a+*+%28%28t+-+1%29+*+t%29+%2F+2%29+solve+for+t
        steps = math.ceil((math.sqrt((diff.amount ** 2) - (4 * diff.amount * start_inc) + (8 * diff.amount * goal) + (4 * (start_inc ** 2))) + diff.amount - (2 * start_inc)) / (2 * diff.amount))
        # Calculate how far user got after those steps
        # current_pos = (start_inc * steps) + (diff.amount * ((steps - 1) * steps) / 2)
        # Calculate length of last step
        current_inc = start_inc + (diff.amount * (steps - 1))
        return (Decimal(steps), current_inc, start_inc / current_inc)
    elif diff.changetype == "multiply":
        # https://en.wikipedia.org/wiki/Geometric_series
        if diff.amount < 1:
            # Calculate max distance travelled, if each step is getting shorter
            max_dist = start_inc / (1 - diff.amount)
            if max_dist < goal:
                return (Decimal("inf"), SV(0), Decimal("inf"))
        # Calculate number of steps required to reach goal
        steps = math.ceil(math.log(-(goal * (1 - diff.amount) / start_inc) + 1, diff.amount))
        # Calculate how far user got after those steps
        # current_pos = start_inc * ((1 - diff.amount ** (steps - 1)) / (1 - diff.amount))
        # Calculate length of last step
        current_inc = start_inc * (diff.amount ** (steps - 1))
        return (Decimal(steps), current_inc, start_inc / current_inc)
    else:
        raise ChangeMethodInvalidException("This change type is not yet supported for scale-walking.")


class ScaleWalkCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        category = "scalestep",
        usage = "<change per step> <distance> [apply]"
    )
    async def scalewalk(self, ctx, change: Diff, dist: SV, flag = None):
        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)
        stats = proportions.PersonStats(userdata)

        stepcount, final_inc, final_ratio = get_steps(stats.walksteplength, change, dist)

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
        category = "scalestep",
        usage = "<change per step> <distance> [apply]"
    )
    async def scalerun(self, ctx, change: Diff, dist: SV, flag = None):
        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)
        stats = proportions.PersonStats(userdata)

        stepcount, final_inc, final_ratio = get_steps(stats.runsteplength, change, dist)

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

    @commands.command(
        category = "scalestep",
        usage = "<change per step>"
    )
    async def setstepscale(self, ctx, change: Diff):
        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)
        userdata.currentscalestep = change
        userdb.save(userdata)
        await ctx.send(f"{userdata.nickname}'s scale per step is now set to {change}.")

    @commands.command(
        category = "scalestep",
        aliases = ["clearstepscale", "unsetstepscale"]
    )
    async def resetstepscale(self, ctx, change: Diff):
        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)
        userdata.currentscalestep = change
        userdb.save(userdata)
        await ctx.send(f"{userdata.nickname}'s scale per step is now cleared.")

    @commands.command(
        category = "scalestep",
    )
    async def step(self, ctx, steps: int = 1):
        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)

        if userdata.currentscalestep.changetype == "add":
            userdata.height += (userdata.currentscalestep.amount * steps)
        elif userdata.currentscalestep.changetype == "multiply":
            userdata.height *= (userdata.currentscalestep.amount ** steps)
        else:
            raise ChangeMethodInvalidException("This change type is not yet supported for scale-walking.")

        # TODO: This needs output. How do you reverse calculate total distance traveled?

        userdb.save(userdata)


def setup(bot):
    bot.add_cog(ScaleWalkCog(bot))
