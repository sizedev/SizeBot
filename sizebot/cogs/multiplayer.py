from copy import copy
import logging
from typing import Union

import discord
from discord.ext import commands

from sizebot.lib import userdb, nickmanager
from sizebot.lib.constants import colors, emojis
from sizebot.lib.diff import Diff
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.errors import ChangeMethodInvalidException
from sizebot.lib.units import SV, WV

logger = logging.getLogger("sizebot")


class MPCog(commands.Cog):
    """Commands to create or clear triggers."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases = ["pb"],
        category = "multiplayer"
    )
    async def pushbutton(self, ctx, user: discord.Member):
        """Push someone's button!

        If a user has a button set (with `&setbutton`,) changes that user by their set amount.
        """
        userdata = userdb.load(ctx.guild.id, user.id)
        if userdata.button is None:
            await ctx.send(f"{userdata.nickname} has no button to push!")
            return
        diff = userdata.button
        if diff.changetype == "multiply":
            userdata.height *= diff.amount
        elif diff.changetype == "add":
            userdata.height += diff.amount
        elif diff.changetype == "power":
            userdata = userdata ** diff.amount
        userdb.save(userdata)
        await nickmanager.nick_update(user)
        await ctx.send(f"You pushed {userdata.nickname}'s button! They are now **{userdata.height:,.3mu}** tall.")

    @commands.command(
        usage = "<diff>",
        category = "multiplayer"
    )
    async def setbutton(self, ctx, *, diff: Diff):
        """Set up a button for others to push!

        Set a change amount, and when others run `&pushbutton` on you, you'll change by that amount.
        """
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        userdata.button = diff
        userdb.save(userdata)
        await ctx.send(f"Set button to {diff}.")

    @commands.command(
        category = "multiplayer",
        aliases = ["resetbutton", "unsetbutton", "removebutton"]
    )
    async def clearbutton(self, ctx):
        """Remove your push button."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        userdata.button = None
        userdb.save(userdata)
        await ctx.send("Your button is now disabled.")

    @commands.command(
        usage = "<amount> <victim> [thief]",
        category = "multiplayer"
    )
    async def steal(self, ctx, amount: Union[SV, WV], victim: discord.Member, thief: discord.Member = None):
        """See what would happen if you stole size from a user.

        `amount` can be a height amount or a weight amount.
        If `thief` is not specified, it defaults to yourself.

        Examples:
        `&steal 1ft @User`
        `&steal 50lb @User @Thief`

        #ALPHA#
        """
        if thief is None:
            thief = ctx.message.author

        thiefdata = userdb.load(ctx.guild.id, thief.id)
        victimdata = userdb.load(ctx.guild.id, victim.id)

        if isinstance(amount, SV):
            original_victim_height = copy(victimdata.height)
            original_victim_weight = copy(victimdata.weight)  # Do these need to be copy()?

            # Stealing too much
            if amount > original_victim_height:
                await ctx.send(f"**{victimdata.nickname}** doesn't have {amount:,.3mu} to steal!")
                return

            # Calculate mass loss
            victimdata.height -= amount
            mass_stolen = original_victim_weight - victimdata.weight

            # Give the mass to the thief
            original_thief_weight = copy(thiefdata.weight)
            new_thief_weight = original_thief_weight + mass_stolen
            ratio = Decimal(new_thief_weight / original_thief_weight)
            ratio = ratio ** Decimal("1/3")  # cube root
            thiefdata.scale *= ratio

        if isinstance(amount, WV):
            original_victim_weight = copy(victimdata.weight)  # Do these need to be copy()?

            # Stealing too much
            if amount > original_victim_weight:
                await ctx.send(f"**{victimdata.nickname}** doesn't have {amount:,.3mu} to steal!")
                return

            # Calculate mass loss
            mass_stolen = original_victim_weight - victimdata.weight

            # Give the mass to the thief
            original_thief_weight = copy(thiefdata.weight)
            new_thief_weight = original_thief_weight + mass_stolen
            ratio = Decimal(new_thief_weight / original_thief_weight)
            ratio = ratio ** Decimal("1/3")  # cube root
            thiefdata.scale *= ratio

        e = discord.Embed(
            title = f"If {thiefdata.nickname} stole {amount:,.3mu} from {victimdata.nickname}...",
            description = (
                f"**{victimdata.nickname}** would now be **{victimdata.height:,.3mu}** tall and weigh **{victimdata.weight:,.3mu}**.\n"
                f"**{thiefdata.nickname}** would now be **{thiefdata.height:,.3mu}** tall and weigh **{thiefdata.weight:,.3mu}**.\n"
            ),
            color = colors.cyan
        )

        await ctx.send(embed = e)

    @commands.command(
        aliases = ["cother", "co"],
        category = "change",
        usage = "<user> <change>"
    )
    async def changeother(self, ctx, other: discord.Member, *, string: Union[Diff]):
        """Change someone else's height. The other user must have this functionality enabled.
        """
        userdata = userdb.load(other.guild.id, other.id)

        if not userdata.allowchangefromothers:
            await ctx.send(f"{userdata.nickname} does not allow others to change their size.")
            return

        style = string.changetype
        amount = string.amount

        userdata = userdb.load(other.guild.id, other.id)
        if style == "add":
            userdata.height += amount
        elif style == "multiply":
            userdata.height *= amount
        elif style == "power":
            userdata = userdata ** amount
        else:
            raise ChangeMethodInvalidException
        await nickmanager.nick_update(other)

        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname} is now {userdata.height:m} ({userdata.height:u}) tall.")

    @commands.command(
        category = "multiplayer"
    )
    async def toggleallowothers(self, ctx):
        """Allow other users to change your size.

        NOTE: THIS HAS NO WHITELIST, BLACKLIST, LIMITS, OR OTHERWISE.
        THIS ALLOWS ANYONE TO CHANGE YOUR SIZE TO ANYTHING.
        YOU HAVE BEEN WARNED.

        #ALPHA#
        """
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        userdata.allowchangefromothers = not userdata.allowchangefromothers
        userdb.save(userdata)

        s = f"Set allowing others to change your size to {userdata.allowchangefromothers}."

        if userdata.allowchangefromothers:
            s += f"""\n{emojis.warning} **NOTE**: THIS HAS NO WHITELIST, BLACKLIST, LIMITS, OR OTHERWISE.
THIS ALLOWS ANYONE TO CHANGE YOUR SIZE TO ANYTHING.
YOU HAVE BEEN WARNED."""
        await ctx.send(s)


async def setup(bot):
    await bot.add_cog(MPCog(bot))
