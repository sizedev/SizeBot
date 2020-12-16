import logging
import re
from copy import copy
from sizebot.lib.utils import tryInt

from discord.ext import commands

from sizebot.lib import userdb
from sizebot.lib.diff import Diff
from sizebot.lib.errors import ChangeMethodInvalidException, UserMessedUpException, ValueIsZeroException


logger = logging.getLogger("sizebot")

re_char = r"(.*)[/:]?|(?:\s*per\s*)?(\d+)?"


class ScaleTypeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases = ["setscaletalk", "setscaletype", "settypescale"],
        category = "scalestep",
        usage = "<change per characters>"
    )
    async def settalkscale(self, ctx, change: str):
        """Set the amount you scale per character.

        Sets the amount that you scale for each character you type.
        Accepts addition or subtraction of a certain height, or multiplication/division of a factor.

        Examples:
        `&settalkscale 2x/100
        `&settalkscale -1mm
        """

        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)

        if match := re.fullmatch(re_char, change):
            diff = Diff.parse(match.group(1))
            if match.group(2):
                chars = tryInt(match.group(2))
            else:
                chars = 1
            if not isinstance(chars, int):
                raise UserMessedUpException(f"`{change}` is not a valid character count.")
        else:
            raise UserMessedUpException(f"`{change}` is not a valid change-per-character.")

        if diff.changetype == "add":
            finaldiff = copy(diff)
            finaldiff.amount = finaldiff.amount / chars
        elif diff.changetype == "multiply":
            finaldiff = copy(diff)
            finaldiff.amount = finaldiff.amount ** (1 / chars)
        else:
            raise ChangeMethodInvalidException("This change type is not yet supported for scale-talking.")

        userdata.currentscaletalk = finaldiff
        if finaldiff.amount == 0:
            raise ValueIsZeroException
        userdb.save(userdata)
        await ctx.send(f"{userdata.nickname}'s scale per character is now set to {finaldiff.original}.")

    @commands.command(
        category = "scalestep",
        aliases = ["clearsteptalk", "unsetsteptalk", "resettalkstep", "cleartalkstep", "unsettalkstep",
                   "clearsteptype", "unsetsteptype", "resettypestep", "cleartypestep", "unsettypestep"]
    )
    async def resetsteptalk(self, ctx):
        """Clear your talk-scale amount."""

        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)
        userdata.currentscaletalk = None
        userdb.save(userdata)
        await ctx.send(f"{userdata.nickname}'s scale per character is now cleared.")


async def on_message(self, message):

    guildid = message.author.guild.id
    userid = message.author.id
    length = len(message.content)

    userdata = userdb.load(guildid, userid)

    if userdata.currentscaletalk is None:
        return

    if userdata.currentscaletalk.changetype == "add":
        userdata.height += (userdata.currentscaletalk.amount * length)
    elif userdata.currentscaletalk.changetype == "multiply":
        userdata.height *= (userdata.currentscaletalk.amount ** length)

    userdb.save(userdata)


def setup(bot):
    bot.add_cog(ScaleTypeCog(bot))
