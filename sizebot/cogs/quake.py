from typing import Literal, NamedTuple

from decimal import Decimal
from discord import Embed
import discord
from discord.ext import commands

from sizebot.lib import userdb
from sizebot.lib.constants import colors, emojis
from sizebot.lib.quake import breath_joules, heartbeat_joules, joules_to_mag, jump_joules, mag_to_name, mag_to_radius, poke_joules, step_joules, stomp_joules, type_joules
from sizebot.lib.stats import StatBox
from sizebot.lib.units import SV
from sizebot.lib.userdb import load_or_fake, FakePlayer
from sizebot.lib.errors import UserMessedUpException

EARTH_RAD = Decimal(10_018_570)
UNI_RAD = Decimal(4.4E26)
QuakeType = Literal["step", "stomp", "jump", "poke", "breath", "breathe", "heartbeat", "type", "typing"]


class QuakeData(NamedTuple):
    verb: str
    print_mag: str
    print_joules: float
    e_type: str
    print_rad: str


def quake_data(userdata: userdb.User, quake_type: QuakeType, scale_rad = 1) -> QuakeData:
    if quake_type == "step":
        verb = " stepping"
        joules = step_joules(userdata)
    elif quake_type == "stomp":
        verb = " stomping"
        joules = stomp_joules(userdata)
    elif quake_type == "jump":
        verb = " jumping"
        joules = jump_joules(userdata)
    elif quake_type == "poke":
        verb = " poking"
        joules = poke_joules(userdata)
    elif quake_type == "breath" or quake_type == "breathe":
        verb = " breathing"
        joules = breath_joules(userdata)
    elif quake_type == "heartbeat":
        verb = "'s heart beating"
        joules = heartbeat_joules(userdata)
    elif quake_type == "type" or quake_type == "typing":
        verb = " typing one letter"
        joules = type_joules(userdata)
    else:
        raise UserMessedUpException(f"{quake_type} is not a valid quake type.")
    mag = joules_to_mag(joules)
    e_type = mag_to_name(mag)
    rad = mag_to_radius(mag)
    rad = SV(rad * scale_rad)
    print_mag = max(mag, Decimal(0.0))
    if rad < EARTH_RAD:
        print_rad = f"{rad:,.1mu}"
    elif rad < UNI_RAD:
        e_rad = rad / EARTH_RAD
        print_rad = f"{e_rad:,.2} 🌎"
    else:
        u_rad = rad / UNI_RAD
        print_rad = f"{u_rad:,.2} {emojis.universe}"
    qd = QuakeData(verb, f"{print_mag:,.1}", f"{joules:,.0}", e_type, print_rad)
    return qd


def quake_embed(userdata: userdb.User, quake_type: QuakeType, scale_rad = 1) -> discord.Embed:
    qd = quake_data(userdata, quake_type, scale_rad)
    e = Embed(
        title=f"Earthquake generated by {userdata.nickname}{qd.verb}",
        description=f"{userdata.nickname} is {userdata.height:,.3mu} tall, and weighs {userdata.weight:,.3mu}.",
        color=colors.cyan
    )
    e.add_field(name = "Magnitude", value = qd.print_mag)
    e.add_field(name = "Joules", value = qd.print_joules)
    e.add_field(name = "Earthquake Type", value = qd.e_type)
    e.add_field(name = "Radius" if (scale_rad == 1) else "Percieved Radius", value = qd.print_rad)
    return e


def quake_stats_embed(userdata: userdb.User, scale_rad = 1) -> discord.Embed:
    e = Embed(
        title=f"Earthquakes generated by {userdata.nickname}",
        description=f"{userdata.nickname} is {userdata.height:,.3mu} tall, and weighs {userdata.weight:,.3mu}.",
        color=colors.cyan
    )
    for qt in ["step", "stomp", "jump", "poke", "breath", "heartbeat", "type"]:
        qd = quake_data(userdata, qt, scale_rad)
        if qt == "step" or qd.print_mag != "0.0":
            e.add_field(name = f"{userdata.nickname}{qd.verb}", value = f"{qd.print_joules}J (Mag {qd.print_mag}, {qd.e_type})")

    return e


class QuakeCog(commands.Cog):
    """Quake commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        aliases = ["quake"],
        usage = "[type] [user/height]",
        category = "stats")
    async def earthquake(self, ctx: commands.Context[commands.Bot], quake_type: QuakeType | None = "step", user: discord.Member | FakePlayer | SV = None):
        """See what quakes would be caused by your steps.\n#ACC#"""
        if user is None:
            user = ctx.author
        userdata = load_or_fake(user)
        e = quake_embed(userdata, quake_type)
        await ctx.send(embed = e)

    @commands.command(
        aliases = ["quakestats"],
        usage = "[user/height]",
        category = "stats")
    async def earthquakestats(self, ctx: commands.Context[commands.Bot], user: discord.Member | FakePlayer | SV = None):
        """See what quakes would be caused by your steps.\n#ACC#"""
        if user is None:
            user = ctx.author
        userdata = load_or_fake(user)
        e = quake_stats_embed(userdata)
        await ctx.send(embed = e)

    @commands.command(
        aliases = ["quakecomp"],
        usage = "[user] [type]",
        category = "stats")
    async def quakecompare(self, ctx: commands.Context[commands.Bot], user: discord.Member | FakePlayer | SV, quake_type: QuakeType | None = "step"):
        """See what quakes would be caused by someone else's steps.\n#ACC#"""
        self_user = load_or_fake(ctx.author)
        userdata = load_or_fake(user)
        userdata.scale *= userdata.viewscale
        e = quake_embed(userdata, quake_type, scale_rad = userdata.viewscale)
        e.title = e.title + f" as seen by {self_user.nickname}"
        e.description = f"To {self_user.nickname}, " + e.description
        await ctx.send(embed = e)

    @commands.command(
        aliases = [],
        usage = "<dist> [user/height]",
        category = "stats")
    async def quakewalk(self, ctx: commands.Context[commands.Bot], dist: SV, user: discord.Member | FakePlayer | SV = None):
        """Walk a distance and cause some quakes.\n#ACC#"""
        if user is None:
            user = ctx.author
        userdata = load_or_fake(user)
        stats = StatBox.load(userdata.stats).scale(userdata.scale)
        steps: int = int(dist / stats['walksteplength'].value)

        if steps < 1:
            await ctx.send("You don't even have to take a single step to reach that distance!")
            return

        small_j = step_joules(userdata)
        small_mag = joules_to_mag(small_j)
        small_type = mag_to_name(small_mag)

        big_j = step_joules(userdata) * steps
        big_mag = joules_to_mag(big_j)
        big_type = mag_to_name(big_mag)

        return_string = (
            f"{userdata.nickname} is {userdata.height:,.3mu} tall, and weighs {userdata.weight:,.3mu}.\n"
            f"Walking {dist:,.1mu}, they would take **{steps:,} steps**, each causing a **Magnitude {small_mag} earthquake.** ({small_type})\n"
            f"That's equivalent to **one Magnitude {big_mag} earthquake**. ({big_type})"
        )

        await ctx.send(return_string)

    @commands.command(
        aliases = [],
        usage = "<string>",
        category = "stats")
    async def quaketype(self, ctx: commands.Context[commands.Bot], s: str):
        """Type a sentence and cause some quakes.\n#ACC#"""
        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)

        steps: int = len(s)

        small_j = type_joules(userdata)
        small_mag = joules_to_mag(small_j)
        small_type = mag_to_name(small_mag)

        big_j = type_joules(userdata) * steps
        big_mag = joules_to_mag(big_j)
        big_type = mag_to_name(big_mag)

        return_string = (
            f"{userdata.nickname} is {userdata.height:,.3mu} tall, and weighs {userdata.weight:,.3mu}.\n"
            f"Typing {steps} characters, {userdata.nickname} caused **{steps:,} Magnitude {small_mag} earthquakes.** ({small_type})\n"
            f"That's equivalent to **one Magnitude {big_mag} earthquake**. ({big_type})"
        )

        await ctx.send(return_string)


async def setup(bot: commands.Bot):
    await bot.add_cog(QuakeCog(bot))
