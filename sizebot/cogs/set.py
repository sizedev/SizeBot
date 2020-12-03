import logging
import typing

import discord
from discord.ext import commands

from sizebot.cogs.register import showNextStep
from sizebot.lib import decimal, errors, proportions, userdb, utils
from sizebot.lib.constants import emojis
from sizebot.lib.diff import Diff
from sizebot.lib.diff import Rate as ParseableRate
from sizebot.lib.proportions import formatShoeSize, fromShoeSize
from sizebot.lib.units import SV, WV

logger = logging.getLogger("sizebot")


class SetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases = ["changenick", "nick"],
        usage = "<nick>",
        category = "set"
    )
    @commands.guild_only()
    async def setnick(self, ctx, *, newnick):
        """Change nickname."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.nickname = newnick
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) changed their nick to {userdata.nickname}.")
        await ctx.send(f"<@{ctx.author.id}>'s nick is now {userdata.nickname}")

        await proportions.nickUpdate(ctx.author)
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<species>",
        category = "set"
    )
    @commands.guild_only()
    async def setspecies(self, ctx, *, newtag):
        """Change species."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.species = newtag
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) changed their species to {userdata.species}.")
        await ctx.send(f"<@{ctx.author.id}>'s species is now a {userdata.species}.")

        await proportions.nickUpdate(ctx.author)
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["clearspecies"],
        category = "set"
    )
    @commands.guild_only()
    async def resetspecies(self, ctx):
        """Remove species."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.species = None
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) removed their species.")
        await ctx.send(f"<@{ctx.author.id}>'s species is now cleared.")

        await proportions.nickUpdate(ctx.author)
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<Y/N>",
        category = "set"
    )
    @commands.guild_only()
    async def setdisplay(self, ctx, newdisp: bool):
        """Set display mode."""
        if newdisp not in [True, False]:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} [Y/N/true/false/yes/no/enable/disable...]`.")
            return

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.display = newdisp
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) set their display to {newdisp}.")
        await ctx.send(f"<@{ctx.author.id}>'s display is now set to {userdata.display}.")

        await proportions.nickUpdate(ctx.author)
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<M/U>",
        category = "set"
    )
    @commands.guild_only()
    async def setsystem(self, ctx, newsys):
        """Set measurement system."""
        newsys = newsys.lower()
        systemmap = {
            "m":         "m",
            "b":         "m",
            "e":         "m",
            "u":         "u",
            "i":         "u",
            "c":         "u",
            "a":         "u",
            "metric":    "m",
            "british":   "m",
            "europe":    "m",
            "us":        "u",
            "imperial":  "u",
            "customary": "u",
            "american":  "u"
        }

        if newsys not in systemmap:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} {ctx.command.usage}`.")
            return

        newsys = systemmap[newsys]
        
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.unitsystem = newsys
        completed_registration = userdata.complete_step("setsystem")
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) set their system to {userdata.unitsystem}.")
        await ctx.send(f"<@{ctx.author.id}>'s system is now set to {userdata.unitsystem}.")

        await proportions.nickUpdate(ctx.author)
        await showNextStep(ctx, userdata, completed=completed_registration)

    @commands.command(
        usage = "<height>",
        category = "set"
    )
    @commands.guild_only()
    async def setheight(self, ctx, *, newheight: SV):
        """Change height."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.height = newheight
        completed_registration = userdata.complete_step("setheight")
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) is now {userdata.height:m} tall.")
        await ctx.send(f"<@{ctx.author.id}> is now {userdata.height:mu} tall.")

        await proportions.nickUpdate(ctx.author)
        await showNextStep(ctx, userdata, completed=completed_registration)

    @commands.command(
        aliases = ["resetsize", "reset"],
        category = "set"
    )
    @commands.guild_only()
    async def resetheight(self, ctx):
        """Reset height/size."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.height = userdata.baseheight
        userdb.save(userdata)

        await ctx.send(f"{ctx.author.display_name} reset their size.")
        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) reset their size.")

        await proportions.nickUpdate(ctx.author)
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<minheight> <maxheight>",
        category = "set"
    )
    @commands.guild_only()
    async def setrandomheight(self, ctx, minheight: SV, maxheight: SV):
        """Change height to a random value.

        Sets your height to a height between `minheight` and `maxheight`.
        Weighted on a logarithmic curve."""
        minheightSV = utils.clamp(0, minheight, SV._infinity)
        maxheightSV = utils.clamp(0, maxheight, SV._infinity)

        newheightSV = decimal.randRangeLog(minheightSV, maxheightSV)

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.height = newheightSV
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) set a random height, and are now {userdata.height:m} tall.")
        await ctx.send(f"<@{ctx.author.id}> is now {userdata.height:mu} tall.")

        await proportions.nickUpdate(ctx.author)
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["inf"],
        category = "set"
    )
    @commands.guild_only()
    async def setinf(self, ctx):
        """Change height to infinity."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.height = "infinity"
        completed_registration = userdata.complete_step("setheight")
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) is now infinitely tall.")
        await ctx.send(f"<@{ctx.author.id}> is now infinitely tall.")

        await proportions.nickUpdate(ctx.author)
        await showNextStep(ctx, userdata, completed=completed_registration)

    @commands.command(
        aliases = ["0"],
        category = "set"
    )
    @commands.guild_only()
    async def set0(self, ctx):
        """Change height to a zero."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.height = 0
        completed_registration = userdata.complete_step("setheight")
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) is now nothing.")
        await ctx.send(f"<@{ctx.author.id}> is now nothing.")

        await proportions.nickUpdate(ctx.author)
        await showNextStep(ctx, userdata, completed=completed_registration)

    @commands.command(
        usage = "<height>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbaseheight(self, ctx, *, newbaseheight: SV):
        """Change base height."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        # Convenience for initial registration
        if "setheight" in userdata.registration_steps_remaining:
            userdata.height = newbaseheight
            if not (SV.parse("4ft") < newbaseheight < SV.parse("8ft")):
                await ctx.send(f"{emojis.warning} **WARNING:** Your base height should probably be something more human-scale. This makes comparison math work out much nicer. If this was intended, you can ignore this warning, but it is ***highly recommended*** that you have a base height similar to the size of a normal human being.")

        userdata.baseheight = newbaseheight
        completed_registration = userdata.complete_step("setheight")
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) changed their base height to {newbaseheight}.")
        await ctx.send(f"<@{ctx.author.id}>'s base height is now {userdata.baseheight:mu} tall.")

        await proportions.nickUpdate(ctx.author)
        await showNextStep(ctx, userdata, completed=completed_registration)

    @commands.command(
        usage = "<weight>",
        category = "set"
    )
    async def setweight(self, ctx, *, newweight: WV):
        """Set your current weight."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.weight = newweight
        completed_registration = userdata.complete_step("setweight")
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) changed their weight to {newweight}.")
        await ctx.send(f"<@{ctx.author.id}>'s weight is now {userdata.weight:mu}")

        await proportions.nickUpdate(ctx.author)
        await showNextStep(ctx, userdata, completed=completed_registration)

    @commands.command(
        usage = "<weight>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbaseweight(self, ctx, *, newbaseweight: WV):
        """Change base weight."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        if "setweight" in userdata.registration_steps_remaining:
            if not (WV.parse("10lb") < newbaseweight < WV.parse("1000lb")):
                await ctx.send(f"{emojis.warning} **WARNING:** Your base weight should probably be something more human-scale. This makes comparison math work out much nicer. If this was intended, you can ignore this warning, but it is ***highly recommended*** that you have a base weight similar to that of a normal human being.")

        userdata.baseweight = newbaseweight
        completed_registration = userdata.complete_step("setweight")
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) changed their base weight to {newbaseweight}.")
        await ctx.send(f"<@{ctx.author.id}>'s base weight is now {userdata.baseweight:mu}")

        await proportions.nickUpdate(ctx.author)
        await showNextStep(ctx, userdata, completed=completed_registration)

    @commands.command(
        usage = "<height/weight> [height/weight]",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbase(self, ctx, arg1: typing.Union[SV, WV], arg2: typing.Union[SV, WV] = None):
        """Set your base height and weight."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        # Don't allow a user to enter setbase(SV, SV) or setbase(WV, WV)
        if (isinstance(arg1, SV) and isinstance(arg2, SV)) or (isinstance(arg1, WV) and isinstance(arg2, WV)):
            raise errors.UserMessedUpException("Please do not enter two heights or two weights.")

        newbaseheight = None
        newbaseweight = None
        for arg in [arg1, arg2]:
            if isinstance(arg, SV):
                newbaseheight = arg
            if isinstance(arg, WV):
                newbaseweight = arg
        completed_registration = False
        if newbaseheight is not None:
            if "setheight" in userdata.registration_steps_remaining:
                userdata.height = newbaseheight
                if not (SV.parse("4ft") < newbaseheight < SV.parse("8ft")):
                    await ctx.send(f"{emojis.warning} **WARNING:** Your base height should probably be something more human-scale. This makes comparison math work out much nicer. If this was intended, you can ignore this warning, but it is ***highly recommended*** that you have a base height similar to the size of a normal human being.")
            userdata.baseheight = newbaseheight
            completed_registration = userdata.complete_step("setheight") or completed_registration
        if newbaseweight is not None:
            if "setweight" in userdata.registration_steps_remaining:
                if not (WV.parse("10lb") < newbaseheight < SV.parse("1000lb")):
                    await ctx.send(f"{emojis.warning} **WARNING:** Your base weight should probably be something more human-scale. This makes comparison math work out much nicer. If this was intended, you can ignore this warning, but it is ***highly recommended*** that you have a base weight similar to that of a normal human being.")
            userdata.baseweight = newbaseweight
            completed_registration = userdata.complete_step("setweight") or completed_registration
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) changed their base height and weight to {userdata.baseheight:,.3mu} and {userdata.baseweight:,.3mu}.")
        await ctx.send(f"{ctx.author.display_name} changed their base height and weight to {userdata.baseheight:,.3mu} and {userdata.baseweight:,.3mu}")
        await showNextStep(ctx, userdata, completed=completed_registration)

    @commands.command(
        usage = "<foot>",
        category = "set"
    )
    async def setfoot(self, ctx, *, newfoot):
        """Set your current foot length."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.footlength = SV(SV.parse(newfoot) * userdata.viewscale)
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s foot is now {userdata.footlength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s foot is now {userdata.footlength:mu} long. ({formatShoeSize(userdata.footlength)})")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbasefoot(self, ctx, *, newfoot: typing.Union[decimal.Decimal, SV]):
        """Set a custom foot length."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.footlength = newfoot
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s foot is now {userdata.footlength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s foot is now {userdata.footlength:mu} long. ({formatShoeSize(userdata.footlength)})")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["setshoesize"],
        usage = "<shoe>",
        category = "set"
    )
    async def setshoe(self, ctx, *, newshoe):
        """Set your current shoe size.

        Accepts a US Shoe Size.
        If a W is in the shoe size anywhere, it is parsed as a Women's size.
        If a C is in the show size anywhere, it is parsed as a Children's size."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        newfoot = fromShoeSize(newshoe)

        userdata.footlength = SV(newfoot * userdata.viewscale)
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s foot is now {userdata.footlength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s foot is now {userdata.footlength:mu} long. ({formatShoeSize(userdata.footlength)})")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["setbaseshoesize"],
        usage = "<length>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbaseshoe(self, ctx, *, newshoe: str):
        """Set a custom base shoe size.

        Accepts a US Shoe Size.
        If a W is in the shoe size anywhere, it is parsed as a Women's size.
        If a C is in the show size anywhere, it is parsed as a Children's size."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        newfoot = fromShoeSize(newshoe)

        userdata.footlength = newfoot
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s foot is now {userdata.footlength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s foot is now {userdata.footlength:mu} long. ({formatShoeSize(userdata.footlength)})")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["clearfoot", "unsetfoot"],
        category = "set"
    )
    @commands.guild_only()
    async def resetfoot(self, ctx):
        """Remove custom foot length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.footlength = None
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) removed their custom foot length.")
        await ctx.send(f"<@{ctx.author.id}>'s foot length is now default.")
        await showNextStep(ctx, userdata)

    @commands.command(
        category = "set"
    )
    @commands.guild_only()
    async def togglepaw(self, ctx):
        """Switch between the word "foot" and "paw" for your stats."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.pawtoggle = not userdata.pawtoggle
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) toggled their foot word to {userdata.footname}.")
        await ctx.send(f"The end of <@{ctx.author.id}>'s legs are now called a {userdata.footname.lower()}.")
        await showNextStep(ctx, userdata)

    @commands.command(
        category = "set"
    )
    @commands.guild_only()
    async def togglefur(self, ctx):
        """Switch between the word "hair" and "fur" for your stats."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.furtoggle = not userdata.furtoggle
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) toggled their hair word to {userdata.hairname}.")
        await ctx.send(f"The hair of <@{ctx.author.id}> is now called {userdata.hairname.lower()}.")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<hair>",
        category = "set"
    )
    async def sethair(self, ctx, *, newhair):
        """Set your current hair length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        newhairsv = SV(SV.parse(newhair) * userdata.viewscale)

        userdata.hairlength = newhairsv
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s hair is now {userdata.hairlength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s hair is now {userdata.hairlength:mu} long.")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbasehair(self, ctx, *, newhair):
        """Set a custom base hair length."""
        newhairsv = SV.parse(newhair)

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.hairlength = newhairsv
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s hair is now {userdata.hairlength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s hair is now {userdata.hairlength:mu} long.")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["clearhair", "unsethair"],
        category = "set"
    )
    @commands.guild_only()
    async def resethair(self, ctx):
        """Remove custom hair length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.hairlength = None
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) removed their custom hair length.")
        await ctx.send(f"<@{ctx.author.id}>'s hair length is now cleared.")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<tail>",
        category = "set"
    )
    async def settail(self, ctx, *, newtail):
        """Set your current tail length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        newtailsv = SV(SV.parse(newtail) * userdata.viewscale)

        userdata.taillength = newtailsv
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s tail is now {userdata.taillength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s tail is now {userdata.taillength:mu} long.")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbasetail(self, ctx, *, newtail):
        """Set a custom tail length."""
        newtailsv = SV.parse(newtail)

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.taillength = newtailsv
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s tail is now {userdata.taillength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s tail is now {userdata.taillength:mu} long.")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["cleartail", "unsettail"],
        category = "set"
    )
    @commands.guild_only()
    async def resettail(self, ctx):
        """Remove custom tail length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.taillength = None
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) removed their custom tail length.")
        await ctx.send(f"<@{ctx.author.id}>'s tail length is now cleared.")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<weight>",
        category = "set"
    )
    async def setstrength(self, ctx, *, newstrength):
        """Set your current lift/carry strength."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.liftstrength = WV(WV.parse(newstrength) * (userdata.viewscale ** 3))
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s strength is now {userdata.liftstrength:m}")
        await ctx.send(f"<@{ctx.author.id}>'s strength is now {userdata.liftstrength:mu}.")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<weight>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbasestrength(self, ctx, *, newstrength: WV):
        """Set a custom lift/carry strength."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.liftstrength = newstrength
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s strength is now {userdata.liftstrength:m}")
        await ctx.send(f"<@{ctx.author.id}>'s strength is now {userdata.liftstrength:mu}.")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["clearstrength", "unsetstrength"],
        category = "set"
    )
    @commands.guild_only()
    async def resetstrength(self, ctx):
        """Remove custom lift/carry strength."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.liftstrength = None
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) removed their custom lift/carry strength.")
        await ctx.send(f"<@{ctx.author.id}>'s lift/carry strength is now cleared.")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "set"
    )
    async def setwalk(self, ctx, *, newwalk: ParseableRate):
        """Set your current walk speed."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.walkperhour = ParseableRate(f"{newwalk.diff.amount * userdata.viewscale}/{newwalk.time}",
                                             Diff(f"{newwalk.diff.amount * userdata.viewscale}", "add", newwalk.diff.amount * userdata.viewscale),
                                             newwalk.time)
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s walk is now {userdata.walkperhour:m}")
        await ctx.send(f"<@{ctx.author.id}>'s walk is now {userdata.walkperhour:mu}.")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbasewalk(self, ctx, *, newwalk: ParseableRate):
        """Set a custom walk speed."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.walkperhour = newwalk
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s walk is now {userdata.walkperhour:m}")
        await ctx.send(f"<@{ctx.author.id}>'s walk is now {userdata.walkperhour:mu}.")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["clearwalk", "unsetwalk"],
        category = "set"
    )
    @commands.guild_only()
    async def resetwalk(self, ctx):
        """Remove custom walk speed."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.walkperhour = None
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) removed their custom walk speed.")
        await ctx.send(f"<@{ctx.author.id}>'s walk speed is now cleared.")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "set"
    )
    async def setrun(self, ctx, *, newrun: ParseableRate):
        """Set your current run speed."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.runperhour = ParseableRate(f"{newrun.diff.amount * userdata.viewscale}/{newrun.time}",
                                            Diff(f"{newrun.diff.amount * userdata.viewscale}", "add", newrun.diff.amount * userdata.viewscale),
                                            newrun.time)
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s run is now {userdata.runperhour:m}")
        await ctx.send(f"<@{ctx.author.id}>'s run is now {userdata.runperhour:mu}.")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbaserun(self, ctx, *, newrun: ParseableRate):
        """Set a custom run speed."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.runperhour = newrun
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s run is now {userdata.runperhour:m}")
        await ctx.send(f"<@{ctx.author.id}>'s run is now {userdata.runperhour:mu}.")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["clearrun", "unsetrun"],
        category = "set"
    )
    @commands.guild_only()
    async def resetrun(self, ctx):
        """Remove custom run speed."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.runperhour = None
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) removed their custom run speed.")
        await ctx.send(f"<@{ctx.author.id}>'s run speed is now cleared.")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<male/female/none>",
        category = "set"
    )
    @commands.guild_only()
    async def setgender(self, ctx, gender):
        """Set gender."""
        guild = ctx.guild
        user = ctx.author

        gendermap = {
            "m":      "m",
            "male":   "m",
            "man":    "m",
            "boy":    "m",
            "f":      "f",
            "female": "f",
            "woman":  "f",
            "girl":   "f",
            "none":   None,
            None:     None
        }
        try:
            gender = gendermap[gender]
        except KeyError:
            raise errors.ArgumentException

        userdata = userdb.load(guild.id, user.id, allow_unreg=True)
        userdata.gender = gender
        userdb.save(userdata)

        if userdata.display:
            await proportions.nickUpdate(user)

        logger.info(f"User {user.id} ({user.display_name}) set their gender to {userdata.gender}.")
        await ctx.send(f"<@{user.id}>'s gender is now set to {userdata.gender}.")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["cleargender", "unsetgender"],
        category = "set"
    )
    @commands.guild_only()
    async def resetgender(self, ctx):
        """Reset gender."""
        guild = ctx.guild
        user = ctx.author

        userdata = userdb.load(guild.id, user.id, allow_unreg=True)
        userdata.gender = None
        userdb.save(userdata)

        if userdata.display:
            await proportions.nickUpdate(user)

        logger.info(f"User {user.id} ({user.display_name}) reset their gender.")
        await ctx.send(f"<@{user.id}>'s gender is now reset.")
        await showNextStep(ctx, userdata)

    @commands.command(
        category = "mod",
        hidden = True
    )
    @commands.guild_only()
    @commands.is_owner()
    async def setmodel(self, ctx, user: discord.Member, *, model):
        userdata = userdb.load(ctx.guild.id, user.id)
        userdata.macrovision_model = model
        userdb.save(userdata)
        await ctx.send(f"{user.display_name}'s model is now {model}.")

    @commands.command(
        aliases = ["resetmodel", "unsetmodel"],
        category = "mod",
        hidden = True
    )
    @commands.guild_only()
    @commands.is_owner()
    async def clearmodel(self, ctx, *, user: discord.Member):
        userdata = userdb.load(ctx.guild.id, user.id)
        userdata.macrovision_model = None
        userdb.save(userdata)
        await ctx.send(f"Cleared {user.display_name}'s model.")

    @commands.command(
        category = "mod",
        hidden = True
    )
    @commands.guild_only()
    @commands.is_owner()
    async def setview(self, ctx, user: discord.Member, *, view):
        userdata = userdb.load(ctx.guild.id, user.id)
        userdata.macrovision_view = view
        userdb.save(userdata)
        await ctx.send(f"{user.display_name}'s view is now {view}.")

    @commands.command(
        aliases = ["resetview", "unsetview"],
        category = "mod",
        hidden = True
    )
    @commands.guild_only()
    @commands.is_owner()
    async def clearview(self, ctx, *, user: discord.Member):
        userdata = userdb.load(ctx.guild.id, user.id)
        userdata.macrovision_view = None
        userdb.save(userdata)
        await ctx.send(f"Cleared {user.display_name}'s view.")


def setup(bot):
    bot.add_cog(SetCog(bot))
