from decimal import Decimal
import typing
from discord import Embed
import discord
from discord.ext import commands

from sizebot.lib.constants import colors
from sizebot.lib.fakeplayer import FakePlayer
from sizebot.lib.quake import breath_joules, joules_to_mag, jump_joules, mag_to_name, mag_to_radius, poke_joules, step_joules, stomp_joules
from sizebot.lib.units import SV
from sizebot.lib.userdb import load_or_fake
from sizebot.lib.errors import UserMessedUpException

EARTH_RAD = 10_018_570
QuakeType = typing.Literal["step", "stomp", "jump"]

class QuakeCog(commands.Cog):
    """Quake commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases = ["quake"],
        usage = "[user/height]",
        category = "stats")
    async def earthquake(self, ctx, quake_type: typing.Optional[QuakeType] = "step", user: typing.Union[discord.Member, FakePlayer, SV] = None):
        """See what quakes would be caused by your steps."""
        if user is None:
            user = ctx.author
        userdata = load_or_fake(user)
        if quake_type == "step":
            verb = "stepping"
            joules = step_joules(userdata)
        elif quake_type == "stomp":
            verb = "stomping"
            joules = stomp_joules(userdata)
        elif quake_type == "jump":
            verb = "jumping"
            joules = jump_joules(userdata)
        elif quake_type == "poke":
            verb = "poking"
            joules = poke_joules(userdata)
        elif quake_type == "breath":
            verb = "breathing"
            joules = breath_joules(userdata)
        else:
            raise UserMessedUpException(f"{quake_type} is not a valid quake type.")
        mag = joules_to_mag(joules)
        e_type = mag_to_name(mag).title()
        rad = mag_to_radius(mag)
        print_mag = max(mag, Decimal(0.0))
        if rad < EARTH_RAD:
            print_rad = f"{rad:,.1mu}"
        else:
            e_rad = rad / EARTH_RAD
            print_rad = f"{e_rad:,.2} 🌎"
        e = Embed(
            title=f"Earthquake generated by {userdata.nickname} {verb}",
            description=f"{userdata.nickname} is {userdata.height:,.3mu} tall, and weighs {userdata.weight:,.3mu}.",
            color=colors.cyan
        )
        e.add_field(name = "Magnitude", value = f"{print_mag:,.1}")
        e.add_field(name = "Joules", value = f"{joules:,.0}")
        e.add_field(name = "Earthquake Type", value = e_type)
        e.add_field(name = "Radius", value = print_rad)

        await ctx.send(embed = e)


async def setup(bot):
    await bot.add_cog(QuakeCog(bot))
