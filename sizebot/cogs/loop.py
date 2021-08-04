import logging
from sizebot.lib.units import SV, TV

from discord.ext import commands

import arrow

from sizebot.lib import userdb
from sizebot.lib.constants import emojis
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.language import ed, ing
from sizebot.lib.proportions import PersonStats
from sizebot.lib.utils import prettyTimeDelta

logger = logging.getLogger("sizebot")


def calc_move_dist(userdata):
    movetype = userdata.currentmovetype
    starttime = userdata.movestarted
    stoptime = userdata.movestop

    now = arrow.now()
    timeelapsed = now - starttime
    elapsed_seconds = timeelapsed.total_seconds()
    stopped = stoptime is not None and elapsed_seconds >= stoptime
    if stopped:
        elapsed_seconds = stoptime

    stats = PersonStats(userdata)
    speed = getattr(stats, f"{movetype}perhour", None)
    if speed is None:
        raise ValueError(f"{movetype}perhour is not an attribute on a PersonStats.")

    persecond = SV(speed / 60 / 60)
    distance = SV(Decimal(elapsed_seconds) * persecond)

    return elapsed_seconds, distance


class LoopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        usage = "<type> stop",
        category = "loop"
    )
    @commands.guild_only()
    async def start(self, ctx, action, stop: TV = None):
        """Keep moving forward -- Walt Disney"""
        movetypes = ["walk", "run", "climb", "crawl", "swim"]
        if action not in movetypes:
            # TODO: Raise a real DigiException here.
            await ctx.send(f"{emojis.warning} {action} is not a recognized movement type.")
            return

        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        if userdata.currentmovetype:
            t, distance = calc_move_dist(userdata)
            nicetime = prettyTimeDelta(t)
            await ctx.send(
                f"{emojis.warning} You're already {ing[userdata.currentmovetype]}.\n"
                f"You've gone **{distance:,.3mu}** so far in **{nicetime}**!"
            )
            return

        userdata.currentmovetype = action
        userdata.movestarted = arrow.now()
        userdata.movestop = stop
        userdb.save(userdata)
        await ctx.send(f"{userdata.nickname} is now {ing[userdata.currentmovetype]}.")

    @commands.command(
        category = "loop"
    )
    @commands.guild_only()
    async def stop(self, ctx):
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        if userdata.currentmovetype is None:
            await ctx.send("You aren't currently moving!")
            return

        t, distance = calc_move_dist(userdata)
        nicetime = prettyTimeDelta(t)
        await ctx.send(f"You stopped {ing[userdata.currentmovetype]}. You {ed[userdata.currentmovetype]} **{distance:,.3mu}** in **{nicetime}!")

        userdata.currentmovetype = None
        userdata.movestarted = None
        userdata.movestop = None
        userdb.save(userdata)

    @commands.command(
        category = "loop"
    )
    @commands.guild_only()
    async def sofar(self, ctx, *, who = None):
        if who is None:
            who = ctx.author
        whoid = who.id
        userdata = userdb.load(ctx.guild.id, whoid)

        if userdata.currentmovetype is None:
            if who == ctx.author:
                await ctx.send("You aren't currently moving!")
            else:
                await ctx.send(f"{userdata.nickname} isn't moving!")
            return

        elapsed_seconds, distance = calc_move_dist(userdata)
        nicetime = prettyTimeDelta(elapsed_seconds)

        out = (f"{userdata.nickname} has been {ing[userdata.currentmovetype]} for **{nicetime}**.\n"
               f"They've gone **{distance:,.3mu}** so far!")

        await ctx.send(out)


def setup(bot):
    bot.add_cog(LoopCog(bot))
