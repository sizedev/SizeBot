from decimal import Decimal
import typing
from discord import Embed
import discord
from discord.ext import commands
from sizebot.lib import proportions
from sizebot.lib import userdb

from sizebot.lib.constants import colors, emojis
from sizebot.lib.fakeplayer import FakePlayer
from sizebot.lib.quake import breath_joules, heartbeat_joules, joules_to_mag, jump_joules, mag_to_name, mag_to_radius, poke_joules, step_joules, stomp_joules, type_joules
from sizebot.lib.units import SV
from sizebot.lib.userdb import load_or_fake
from sizebot.lib.errors import UserMessedUpException

EARTH_RAD = Decimal(10_018_570)
UNI_RAD = Decimal(4.4E26)
QuakeType = typing.Literal["step", "stomp", "jump", "poke", "breath", "breathe", "heartbeat", "type", "typing"]

class QuakeCog(commands.Cog):
    """Quake commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases = ["quake"],
        usage = "[type] [user/height]",
        category = "stats")
    async def earthquake(self, ctx, quake_type: typing.Optional[QuakeType] = "step", user: typing.Union[discord.Member, FakePlayer, SV] = None):
        """See what quakes would be caused by your steps."""
        if user is None:
            user = ctx.author
        userdata = load_or_fake(user)
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
        e_type = mag_to_name(mag).title()
        rad = mag_to_radius(mag)
        print_mag = max(mag, Decimal(0.0))
        if rad < EARTH_RAD:
            print_rad = f"{rad:,.1mu}"
        elif rad < UNI_RAD:
            e_rad = rad / EARTH_RAD
            print_rad = f"{e_rad:,.2} 🌎"
        else:
            u_rad = rad / UNI_RAD
            print_rad = f"{u_rad:,.2} {emojis.universe}"
        e = Embed(
            title=f"Earthquake generated by {userdata.nickname}{verb}",
            description=f"{userdata.nickname} is {userdata.height:,.3mu} tall, and weighs {userdata.weight:,.3mu}.",
            color=colors.cyan
        )
        e.add_field(name = "Magnitude", value = f"{print_mag:,.1}")
        e.add_field(name = "Joules", value = f"{joules:,.0}")
        e.add_field(name = "Earthquake Type", value = e_type)
        e.add_field(name = "Radius", value = print_rad)

        await ctx.send(embed = e)

    @commands.command(aliases = [],
        usage = "<dist> [user/height]",
        category = "stats")
    async def quakewalk(self, ctx, dist: SV, user: typing.Union[discord.Member, FakePlayer, SV] = None):
        """Walk a distance and cause some quakes."""
        if user is None:
            user = ctx.author
        userdata = load_or_fake(user)
        stats = proportions.PersonStats(userdata)
        steps: int = int(dist / stats.walksteplength)

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
            f"Walking {dist:,.1mu}, they would take **{steps} steps**, each causing a **Magnitude {small_mag} earthquake.** ({small_type})\n"
            f"That's equivalent to **one Magnitude {big_mag} earthquake**. ({big_type})\n"
        )

        await ctx.send(return_string)

    @commands.command(aliases = [],
        usage = "<string>",
        category = "stats")
    async def quaketype(self, ctx, s: str):
        """Walk a distance and cause some quakes."""
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
            f"Typing {steps} characters, {userdata.nickname} caused **{steps} Magnitude {small_mag} earthquakes.** ({small_type})\n"
            f"That's equivalent to **one Magnitude {big_mag} earthquake**. ({big_type})\n"
        )

        await ctx.send(return_string)


async def setup(bot):
    await bot.add_cog(QuakeCog(bot))
