import logging
import re
from copy import copy
from sizebot.lib.utils import tryInt

import discord
from discord.ext import commands

from sizebot.lib import userdb
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.diff import Diff
from sizebot.lib.errors import ChangeMethodInvalidException, UserMessedUpException, UserNotFoundException, ValueIsZeroException
from sizebot.lib.units import SV


logger = logging.getLogger("sizebot")

re_char = r"(.*)(?:[/:]|\s*per\s*)(\d+)?"


class ScaleTypeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases = ["setscaletalk", "setscaletype", "settypescale"],
        category = "scalestep",
        usage = "<change per characters>"
    )
    async def settalkscale(self, ctx, *, change: str):
        """Set the amount you scale per character.

        Sets the amount that you scale for each character you type.
        Accepts addition or subtraction of a certain height, or multiplication/division of a factor.

        Examples:
        `&settalkscale 2x/100`
        `&settalkscale -1mm` (defaults to per 1 character)
        """

        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)

        chars = None  # fix unbound error
        if match := re.fullmatch(re_char, change):
            diff = Diff.parse(match.group(1))
            if match.group(2):
                chars = tryInt(match.group(2))
                if chars == "":
                    chars = 1
        else:
            raise UserMessedUpException(f"`{change}` is not a valid character count.")
        if not isinstance(chars, int):
            raise UserMessedUpException(f"`{change}` is not a valid character count.")
        elif chars == 0:
            raise ValueIsZeroException

        if diff.changetype == "add":
            finaldiff = copy(diff)
            finaldiff.amount = SV(finaldiff.amount / chars)
        elif diff.changetype == "multiply":
            finaldiff = copy(diff)
            finaldiff.amount = finaldiff.amount ** Decimal(1 / chars)
        else:
            raise ChangeMethodInvalidException("This change type is not yet supported for scale-talking.")

        if finaldiff.amount == 0:
            raise ValueIsZeroException

        userdata.currentscaletalk = finaldiff
        userdata.scaletalklock = True

        userdb.save(userdata)
        if finaldiff.changetype == "multiply":
            await ctx.send(f"{userdata.nickname}'s scale per character is now set to **~{finaldiff.amount:,.10}x**.")
        else:
            await ctx.send(f"{userdata.nickname}'s scale per character is now set to **{finaldiff.amount:,.3mu}**.")

    @commands.command(
        category = "scalestep",
        aliases = ["cleartalkscale", "unsettalkscale", "resetscaletalk", "clearscaletalk", "unsetscaletalk",
                   "cleartypescale", "unsettypescale", "resetscaletype", "clearscaletype", "unsetscaletype",
                   "resettypescale"]
    )
    async def resettalkscale(self, ctx):
        """Clear your talk-scale amount."""

        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)
        userdata.currentscaletalk = None
        userdb.save(userdata)
        await ctx.send(f"{userdata.nickname}'s scale per character is now cleared.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not isinstance(message.author, discord.Member):
            return
        guildid = message.author.guild.id
        userid = message.author.id
        content = message.content
        content = re.sub(r"<:(.*):\d+>", r"\1", content)  # Make emojis just their name.
        length = len(content)

        try:
            userdata = userdb.load(guildid, userid)
        except UserNotFoundException:
            return

        if userdata.scaletalklock is True:
            userdata.scaletalklock = False
            userdb.save(userdata)
            return

        if userdata.currentscaletalk is None:
            return

        if userdata.currentscaletalk.changetype == "add":
            userdata.height += (userdata.currentscaletalk.amount * length)
        elif userdata.currentscaletalk.changetype == "multiply":
            userdata.height *= (userdata.currentscaletalk.amount ** length)

        userdb.save(userdata)


def setup(bot):
    bot.add_cog(ScaleTypeCog(bot))
