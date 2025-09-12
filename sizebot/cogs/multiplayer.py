from copy import copy
import logging
import random

import discord
from discord.ext import commands

from sizebot.lib import userdb, nickmanager
from sizebot.lib.constants import colors, emojis
from sizebot.lib.diff import Diff
from sizebot.lib.errors import ChangeMethodInvalidException, UserNotFoundException
from sizebot.lib.types import BotContext, GuildContext
from sizebot.lib.units import SV, WV, Decimal
from sizebot.lib.utils import map_range

logger = logging.getLogger("sizebot")


class MPCog(commands.Cog):
    """Commands to create or clear triggers."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        aliases = ["pb"],
        category = "multiplayer"
    )
    @commands.guild_only()
    async def pushbutton(self, ctx: GuildContext, user: discord.Member):
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
    @commands.guild_only()
    async def setbutton(self, ctx: GuildContext, *, diff: Diff):
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
    @commands.guild_only()
    async def clearbutton(self, ctx: GuildContext):
        """Remove your push button."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        userdata.button = None
        userdb.save(userdata)
        await ctx.send("Your button is now disabled.")

    @commands.command(
        usage = "<amount> <victim> [thief]",
        category = "multiplayer"
    )
    @commands.guild_only()
    async def steal(self, ctx: GuildContext, amount: SV | WV, victim: discord.Member, thief: discord.Member = None):
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
        category = "multiplayer",
        usage = "<user> <change>"
    )
    @commands.guild_only()
    async def changeother(self, ctx: GuildContext, other: discord.Member, *, string: Diff):
        """Change someone else's height. The other user must have this functionality enabled."""
        userdata = userdb.load(other.guild.id, other.id)

        if not userdata.allowchangefromothers:
            await ctx.send(f"{userdata.nickname} does not allow others to change their size.")
            return

        style = string.changetype
        amount = string.amount

        if style == "add":
            userdata.height += amount
        elif style == "multiply":
            userdata.height *= amount
        elif style == "power":
            userdata = userdata ** amount
        else:
            raise ChangeMethodInvalidException(style)
        await nickmanager.nick_update(other)

        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname} is now {userdata.height:mu} tall.")

    @commands.command(
        aliases = ["sother", "so"],
        usage = "<user> <height>",
        category = "multiplayer"
    )
    @commands.guild_only()
    async def setother(self, ctx: GuildContext, other: discord.Member, *, newheight: SV):
        """Set someone else's height. The other user must have this functionality enabled."""
        userdata = userdb.load(other.guild.id, other.id)

        if not userdata.allowchangefromothers:
            await ctx.send(f"{userdata.nickname} does not allow others to change their size.")
            return

        userdata.height = newheight
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname} is now {userdata.height:mu} tall.")

        await nickmanager.nick_update(other)

    @commands.command(
        category = "multiplayer",
        usage = "<power> [user]"
    )
    @commands.guild_only()
    async def shrinkray(self, ctx: GuildContext, level: int, user: discord.Member | None = None):
        """Zap! Shrink a user with power 1-10."""
        if user is None:
            user = ctx.author
        userdata = userdb.load(user.guild.id, user.id)

        if not userdata.allowchangefromothers:
            await ctx.send(f"{userdata.nickname} does not allow others to change their size.")
            return

        if level == 0:
            await ctx.send("The shrink ray is off...")
            return
        if level < 0:
            await ctx.send("Did you mean to use the growth ray?")
            return
        if level > 11:
            await ctx.send("Don't overpower the shrink ray!")
            return

        level_was_11 = level == 11
        original_level = level
        crit = random.random() < 0.05

        randomness = map_range(random.random(), 0, 1, 0.75, 1.25)
        level = level + (1 if crit else 0)
        level: float = level * randomness

        amount = 0.9 ** (level * (1 + (level / 5)))

        userdata.height = SV(userdata.height * amount)

        await nickmanager.nick_update(user)
        userdb.save(userdata)

        self_nick = ctx.author.display_name
        try:
            self_data = userdb.load(ctx.guild.id, ctx.author.id)
            self_nick = self_data.nickname
        except UserNotFoundException:
            pass

        outstring = f"{self_nick} cranks the shrink ray to {original_level}..."
        if level_was_11:
            outstring += "\n-# *Wait, it goes up that high?!*"
        if ctx.author.id == user.id:
            outstring += "and zaps themselves!"
        else:
            outstring += f"and zaps {userdata.nickname}!"
        if crit:
            outstring += f" And it's a critical hit! They are now {userdata.height:mu} tall."
        else:
            outstring += f" They are now {userdata.height:mu} tall."

        await ctx.send(outstring)

    @commands.command(
        category = "multiplayer",
        usage = "<power> [user]"
    )
    @commands.guild_only()
    async def growthray(self, ctx: GuildContext, level: int, user: discord.Member | None = None):
        """Zap! Grow a user with power 1-10."""
        if user is None:
            user = ctx.author
        userdata = userdb.load(user.guild.id, user.id)

        if not userdata.allowchangefromothers:
            await ctx.send(f"{userdata.nickname} does not allow others to change their size.")
            return

        if level == 0:
            await ctx.send("The growth ray is off...")
            return
        if level < 0:
            await ctx.send("Did you mean to use the shrink ray?")
            return
        if level > 11:
            await ctx.send("Don't overpower the growth ray!")
            return

        level_was_11 = level == 11
        original_level = level
        crit = random.random() < 0.05

        randomness = map_range(random.random(), 0, 1, 0.75, 1.25)
        level = level + (1 if crit else 0)
        level: float = level * randomness

        amount = 1.1 ** (level * (1 + (level / 5)))

        userdata.height = SV(userdata.height * amount)

        await nickmanager.nick_update(user)
        userdb.save(userdata)

        self_nick = ctx.author.display_name
        try:
            self_data = userdb.load(ctx.guild.id, ctx.author.id)
            self_nick = self_data.nickname
        except UserNotFoundException:
            pass

        outstring = f"{self_nick} cranks the growth ray to {original_level}..."
        if level_was_11:
            outstring += "\n-# *Wait, it goes up that high?!*"
        if ctx.author.id == user.id:
            outstring += "and zaps themselves!"
        else:
            outstring += f"and zaps {userdata.nickname}!"
        if crit:
            outstring += f" And it's a critical hit! They are now {userdata.height:mu} tall."
        else:
            outstring += f" They are now {userdata.height:mu} tall."

        await ctx.send(outstring)

    @commands.command(
        category = "multiplayer"
    )
    @commands.guild_only()
    async def toggleallowothers(self, ctx: GuildContext):
        """Allow other users to change your size.

        NOTE: THIS HAS NO WHITELIST OR BLACKLIST.
        THIS ALLOWS ANYONE TO CHANGE YOUR SIZE TO ANYTHING WITHIN YOUR LIMITS.
        YOU HAVE BEEN WARNED.

        #ALPHA#
        """
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        userdata.allowchangefromothers = not userdata.allowchangefromothers
        userdb.save(userdata)

        s = f"Set allowing others to change your size to {userdata.allowchangefromothers}."

        if userdata.allowchangefromothers:
            s += f"""\n{emojis.warning} **NOTE**: THIS HAS NO WHITELIST OR BLACKLIST.
THIS ALLOWS ANYONE TO CHANGE YOUR SIZE TO ANYTHING WITHIN YOUR LIMITS.
YOU HAVE BEEN WARNED."""
        await ctx.send(s)

    @commands.command(
        category = "multiplayer"
    )
    @commands.guild_only()
    async def toggleallowmatching(self, ctx: GuildContext):
        """Allow other users to match your size.
        """
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        userdata.allow_matching = not userdata.allow_matching
        userdb.save(userdata)

        s = f"Set allowing matching of your size to {userdata.allow_matching}."
        await ctx.send(s)


async def setup(bot: commands.Bot):
    await bot.add_cog(MPCog(bot))
