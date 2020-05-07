import logging
import typing

from sizebot.discordplus import commands

from sizebot.lib import decimal, errors, proportions, userdb, utils
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
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.nickname = newnick
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) changed their nick to {userdata.nickname}.")
        await ctx.send(f"<@{ctx.author.id}>'s nick is now {userdata.nickname}")

        await proportions.nickUpdate(ctx.author)

    @commands.command(
        usage = "<species>",
        category = "set"
    )
    @commands.guild_only()
    async def setspecies(self, ctx, *, newtag):
        """Change species."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.species = newtag
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) changed their species to {userdata.species}.")
        await ctx.send(f"<@{ctx.author.id}>'s species is now a {userdata.species}.")

        await proportions.nickUpdate(ctx.author)

    @commands.command(
        aliases = ["clearspecies"],
        category = "set"
    )
    @commands.guild_only()
    async def resetspecies(self, ctx):
        """Remove species."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.species = None
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) removed their species.")
        await ctx.send(f"<@{ctx.author.id}>'s species is now cleared.")

        await proportions.nickUpdate(ctx.author)

    @commands.command(
        usage = "<Y/N>",
        category = "set"
    )
    @commands.guild_only()
    async def setdisplay(self, ctx, newdisp):
        """Set display mode."""
        newdisp = newdisp.upper()
        if newdisp not in ["Y", "N"]:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} [Y/N]`.")
            return

        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.display = newdisp
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) set their display to {newdisp}.")
        await ctx.send(f"<@{ctx.author.id}>'s display is now set to {userdata.display}.")

        await proportions.nickUpdate(ctx.author)

    @commands.command(
        usage = "<M/U>",
        category = "set"
    )
    @commands.guild_only()
    async def setsystem(self, ctx, newsys):
        """Set measurement system."""
        newsys = newsys.lower()
        if newsys not in ["m", "u"]:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} [u/i/m]`.")
            return

        if newsys == "i":
            newsys == "u"

        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.unitsystem = newsys
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) set their system to {userdata.unitsystem}.")
        await ctx.send(f"<@{ctx.author.id}>'s system is now set to {userdata.unitsystem}.")

        await proportions.nickUpdate(ctx.author)

    @commands.command(
        usage = "<height>",
        category = "set"
    )
    @commands.guild_only()
    async def setheight(self, ctx, *, newheight):
        """Change height."""
        newheightsv = SV.parse(newheight)

        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.height = newheightsv
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) is now {userdata.height:m} tall.")
        await ctx.send(f"<@{ctx.author.id}> is now {userdata.height:mu} tall.")

        await proportions.nickUpdate(ctx.author)

    @commands.command(
        aliases = ["resetsize", "reset"],
        category = "set"
    )
    @commands.guild_only()
    async def resetheight(self, ctx):
        """Reset height/size."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.height = userdata.baseheight
        userdb.save(userdata)

        await ctx.send(f"{ctx.author.display_name} reset their size.")
        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) reset their size.")

        await proportions.nickUpdate(ctx.author)

    @commands.command(
        usage = "<minheight> <maxheight>",
        category = "set"
    )
    @commands.guild_only()
    async def setrandomheight(self, ctx, minheight, maxheight):
        """Change height to a random value.

        Sets your height to a height between `minheight` and `maxheight`.
        Weighted on a logarithmic curve."""
        minheightSV = utils.clamp(0, SV.parse(minheight), SV._infinity)
        maxheightSV = utils.clamp(0, SV.parse(maxheight), SV._infinity)

        newheightSV = decimal.randRangeLog(minheightSV, maxheightSV)

        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.height = newheightSV
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) set a random height, and are now {userdata.height:m} tall.")
        await ctx.send(f"<@{ctx.author.id}> is now {userdata.height:mu} tall.")

        await proportions.nickUpdate(ctx.author)

    @commands.command(
        aliases = ["inf"],
        category = "set"
    )
    @commands.guild_only()
    async def setinf(self, ctx):
        """Change height to infinity."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.height = "infinity"
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) is now infinitely tall.")
        await ctx.send(f"<@{ctx.author.id}> is now infinitely tall.")

        await proportions.nickUpdate(ctx.author)

    @commands.command(
        aliases = ["0"],
        category = "set"
    )
    @commands.guild_only()
    async def set0(self, ctx):
        """Change height to a zero."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.height = 0
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) is now nothing.")
        await ctx.send(f"<@{ctx.author.id}> is now nothing.")

        await proportions.nickUpdate(ctx.author)

    @commands.command(
        usage = "<height>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbaseheight(self, ctx, *, newbaseheight):
        """Change base height."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.baseheight = SV.parse(newbaseheight)
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) changed their base height to {newbaseheight}.")
        await ctx.send(f"<@{ctx.author.id}>'s base height is now {userdata.baseheight:mu} tall.")

        await proportions.nickUpdate(ctx.author)

    @commands.command(
        usage = "<weight>",
        category = "set"
    )
    async def setweight(self, ctx, *, newweight):
        """Set your current weight."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.baseweight = WV(WV.parse(newweight) * (userdata.viewscale ** 3))
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) changed their weight to {newweight}.")
        await ctx.send(f"<@{ctx.author.id}>'s weight is now {userdata.weight:mu}")

        await proportions.nickUpdate(ctx.author)

    @commands.command(
        usage = "<weight>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbaseweight(self, ctx, *, newbaseweight):
        """Change base weight."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.baseweight = WV.parse(newbaseweight)
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) changed their base weight to {newbaseweight}.")
        await ctx.send(f"<@{ctx.author.id}>'s base weight is now {userdata.baseweight:mu}")

        await proportions.nickUpdate(ctx.author)

    @commands.command(
        usage = "<height/weight> [height/weight]",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbase(self, ctx, arg1: typing.Union[SV, WV], arg2: typing.Union[SV, WV] = None):
        """Set your base height and weight."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        # Don't allow a user to enter setbase(SV, SV) or setbase(WV, WV)
        if (isinstance(arg1, SV) and isinstance(arg2, SV)) or (isinstance(arg1, WV) and isinstance(arg2, WV)):
            raise errors.UserMessedUpException("Please do not enter two heights or two weights.")

        for arg in [arg1, arg2]:
            if isinstance(arg, SV):
                userdata.baseheight = arg
            if isinstance(arg, WV):
                userdata.baseweight = arg
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) changed their base height and weight to {userdata.baseheight:,.3mu} and {userdata.baseweight:,.3mu}.")
        await ctx.send(f"{ctx.author.display_name} changed their base height and weight to {userdata.baseheight:,.3mu} and {userdata.baseweight:,.3mu}")

    @commands.command(
        usage = "<foot>",
        category = "set"
    )
    async def setfoot(self, ctx, *, newfoot):
        """Set your current foot length."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.footlength = SV(SV.parse(newfoot) * userdata.viewscale)
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s foot is now {userdata.footlength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s foot is now {userdata.footlength:mu} long. ({formatShoeSize(userdata.footlength)})")

    @commands.command(
        usage = "<length>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbasefoot(self, ctx, *, newfoot: typing.Union[decimal.Decimal, SV]):
        """Set a custom foot length."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.footlength = newfoot
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s foot is now {userdata.footlength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s foot is now {userdata.footlength:mu} long. ({formatShoeSize(userdata.footlength)})")

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

        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        newfoot = fromShoeSize(newshoe)

        userdata.footlength = SV(newfoot * userdata.viewscale)
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s foot is now {userdata.footlength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s foot is now {userdata.footlength:mu} long. ({formatShoeSize(userdata.footlength)})")

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

        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        newfoot = fromShoeSize(newshoe)

        userdata.footlength = newfoot
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s foot is now {userdata.footlength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s foot is now {userdata.footlength:mu} long. ({formatShoeSize(userdata.footlength)})")

    @commands.command(
        aliases = ["clearfoot", "unsetfoot"],
        category = "set"
    )
    @commands.guild_only()
    async def resetfoot(self, ctx):
        """Remove custom foot length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.footlength = None
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) removed their custom foot length.")
        await ctx.send(f"<@{ctx.author.id}>'s foot length is now default.")

    @commands.command(
        usage = "<hair>",
        category = "set"
    )
    async def sethair(self, ctx, *, newhair):
        """Set your current hair length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        newhairsv = SV(SV.parse(newhair) * userdata.viewscale)

        userdata.hairlength = newhairsv
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s hair is now {userdata.hairlength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s hair is now {userdata.hairlength:mu} long.")

    @commands.command(
        usage = "<length>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbasehair(self, ctx, *, newhair):
        """Set a custom base hair length."""
        newhairsv = SV.parse(newhair)

        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.hairlength = newhairsv
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s hair is now {userdata.hairlength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s hair is now {userdata.hairlength:mu} long.")

    @commands.command(
        aliases = ["clearhair", "unsethair"],
        category = "set"
    )
    @commands.guild_only()
    async def resethair(self, ctx):
        """Remove custom hair length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.hairlength = None
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) removed their custom hair length.")
        await ctx.send(f"<@{ctx.author.id}>'s hair length is now cleared.")

    @commands.command(
        usage = "<tail>",
        category = "set"
    )
    async def settail(self, ctx, *, newtail):
        """Set your current tail length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        newtailsv = SV(SV.parse(newtail) * userdata.viewscale)

        userdata.taillength = newtailsv
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s tail is now {userdata.taillength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s tail is now {userdata.taillength:mu} long.")

    @commands.command(
        usage = "<length>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbasetail(self, ctx, *, newtail):
        """Set a custom tail length."""
        newtailsv = SV.parse(newtail)

        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.taillength = newtailsv
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s tail is now {userdata.taillength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s tail is now {userdata.taillength:mu} long.")

    @commands.command(
        aliases = ["cleartail", "unsettail"],
        category = "set"
    )
    @commands.guild_only()
    async def resettail(self, ctx):
        """Remove custom tail length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.taillength = None
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) removed their custom tail length.")
        await ctx.send(f"<@{ctx.author.id}>'s tail length is now cleared.")

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

        userdata = userdb.load(guild.id, user.id)
        userdata.gender = gender
        userdb.save(userdata)

        if userdata.display:
            await proportions.nickUpdate(user)

        logger.info(f"User {user.id} ({user.display_name}) set their gender to {userdata.gender}.")
        await ctx.send(f"<@{user.id}>'s gender is now set to {userdata.gender}.")

    @commands.command(
        aliases = ["cleargender", "unsetgender"],
        category = "set"
    )
    @commands.guild_only()
    async def resetgender(self, ctx):
        """Reset gender."""
        guild = ctx.guild
        user = ctx.author

        userdata = userdb.load(guild.id, user.id)
        userdata.gender = None
        userdb.save(userdata)

        if userdata.display:
            await proportions.nickUpdate(user)

        logger.info(f"User {user.id} ({user.display_name}) reset their gender.")
        await ctx.send(f"<@{user.id}>'s gender is now reset.")


def setup(bot):
    bot.add_cog(SetCog(bot))
