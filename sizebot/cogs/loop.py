from typing import cast
from sizebot.lib.types import BotContext

import logging

import arrow

import discord
from discord.ext import commands

from sizebot.lib.speed import MoveType
from sizebot.lib.stats import StatBox
from sizebot.lib.units import SV, TV
from sizebot.lib import userdb
from sizebot.lib.constants import emojis
from sizebot.lib.utils import pretty_time_delta
import sizebot.lib.language as lang

logger = logging.getLogger("sizebot")


def calc_move_dist(userdata: userdb.User) -> tuple[TV, SV]:
    movetype = userdata.currentmovetype
    starttime = userdata.movestarted
    stoptime = userdata.movestop

    now = arrow.now()
    timeelapsed = now - starttime
    elapsed_seconds = TV(timeelapsed.total_seconds())
    if stoptime is not None and elapsed_seconds >= stoptime:
        elapsed_seconds = stoptime

    stats = StatBox.load(userdata.stats).scale(userdata.scale)
    try:
        speed: SV = stats[f"{movetype}perhour"].value
    except KeyError:
        raise ValueError(f"{movetype}perhour is not a valid stat.")

    persecond = SV(speed / 60 / 60)
    distance = SV(elapsed_seconds * persecond)

    return elapsed_seconds, distance


class LoopCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        usage = "<type> [stop]",
        category = "loop"
    )
    @commands.guild_only()
    async def start(self, ctx: BotContext, action: str, stop: TV | None = None):
        """Keep moving forward -- Walt Disney

        `<type>` can be one of the following: walk, run, climb, crawl, swim
        `[stop]` is an optional time limit for moving.
        """
        movetypes = ["walk", "run", "climb", "crawl", "swim"]
        if action not in movetypes:
            # TODO: Raise a real DigiException here.
            await ctx.send(f"{emojis.warning} {action} is not a recognized movement type.")
            return

        # Fix typing now that we've checked it
        action = cast(MoveType, action)

        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        if userdata.currentmovetype:
            t, distance = calc_move_dist(userdata)
            nicetime = pretty_time_delta(t)
            await ctx.send(
                f"{emojis.warning} You're already {lang.ing[userdata.currentmovetype]}.\n"
                f"You've gone **{distance:,.3mu}** so far in **{nicetime}**!"
            )
            return

        userdata.currentmovetype = action
        userdata.movestarted = arrow.now()
        userdata.movestop = stop
        userdb.save(userdata)
        await ctx.send(f"{userdata.nickname} is now {lang.ing[userdata.currentmovetype]}.")

    @commands.command(
        category = "loop"
    )
    @commands.guild_only()
    async def stop(self, ctx: BotContext):
        """Stop a current movement."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        if userdata.currentmovetype is None:
            await ctx.send("You aren't currently moving!")
            return

        t, distance = calc_move_dist(userdata)
        nicetime = pretty_time_delta(t)
        await ctx.send(f"You stopped {lang.ing[userdata.currentmovetype]}. You {lang.ed[userdata.currentmovetype]} **{distance:,.3mu}** in **{nicetime}**!")

        userdata.currentmovetype = None
        userdata.movestarted = None
        userdata.movestop = None
        userdb.save(userdata)

    @commands.command(
        category = "loop"
    )
    @commands.guild_only()
    async def sofar(self, ctx: BotContext, *, who: discord.Member | None = None):
        """How far have you moved so far? [See help.]

        #ALPHA#
        """
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
        nicetime = pretty_time_delta(elapsed_seconds)

        out = (f"{userdata.nickname} has been {lang.ing[userdata.currentmovetype]} for **{nicetime}**.\n"
               f"They've gone **{distance:,.3mu}** so far!")

        await ctx.send(out)


async def setup(bot: commands.Bot):
    await bot.add_cog(LoopCog(bot))
