import logging
import typing

from discord.ext import commands
from sizebot.discordplus import commandsplus

from sizebot.lib import decimal, errors, proportions, userdb, utils
from sizebot.lib.proportions import fromShoeSize
from sizebot.lib.units import SV, WV

logger = logging.getLogger("sizebot")


class SetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commandsplus.command(
        aliases = ["changenick", "nick"],
        usage = "<nick>"
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

    @commandsplus.command(
        usage = "<species>"
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

    @commandsplus.command()
    @commands.guild_only()
    async def clearspecies(self, ctx):
        """Remove species."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.species = None
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) removed their species.")
        await ctx.send(f"<@{ctx.author.id}>'s species is now cleared.")

        await proportions.nickUpdate(ctx.author)

    @commandsplus.command(
        usage = "<height>"
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

    @commandsplus.command(
        aliases = ["resetheight", "reset"]
    )
    @commands.guild_only()
    async def resetsize(self, ctx):
        """Reset size."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.height = userdata.baseheight
        userdb.save(userdata)

        await ctx.send(f"{ctx.author.display_name} reset their size.")
        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) reset their size.")

        await proportions.nickUpdate(ctx.author)

    @commandsplus.command(
        usage = "<Y/N>"
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

    @commandsplus.command(
        usage = "<M/U>"
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

    @commandsplus.command(
        usage = "<minheight> <maxheight>"
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

    @commandsplus.command(
        aliases = ["inf"]
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

    @commandsplus.command(
        aliases = ["0"]
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

    @commandsplus.command(
        usage = "<height>"
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

    @commandsplus.command(
        usage = "<weight>"
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

    @commandsplus.command(
        usage = "<height/weight> [height/weight]"
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

    @commandsplus.command(
        usage = "<length>"
    )
    @commands.guild_only()
    async def setfoot(self, ctx, *, newfoot: typing.Union[decimal.Decimal, SV]):
        """Set a custom foot length.
        
        Accepts either a length or a US Shoe Size."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        if isinstance(newfoot, decimal.Decimal):
            newfoot = fromShoeSize(newfoot)

        userdata.footlength = newfoot
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s foot is now {userdata.footlength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s foot is now {userdata.footlength:mu} long. ({formatShoeSize(userdata.footlength)})")

    @commandsplus.command(
        aliases = ["clearfoot", "unsetfoot"]
    )
    @commands.guild_only()
    async def resetfoot(self, ctx):
        """Remove custom foot length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.footlength = None
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) removed their custom foot length.")
        await ctx.send(f"<@{ctx.author.id}>'s foot length is now default.")

    @commandsplus.command(
        usage = "<length>"
    )
    @commands.guild_only()
    async def sethair(self, ctx, *, newhair):
        """Set a custom hair length."""
        newhairsv = SV.parse(newhair)

        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.hairlength = newhairsv
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s hair is now {userdata.hairlength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s hair is now {userdata.hairlength:mu} long.")

    @commandsplus.command(
        aliases = ["clearhair", "unsethair"]
    )
    @commands.guild_only()
    async def resethair(self, ctx):
        """Remove custom hair length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.hairlength = None
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) removed their custom hair length.")
        await ctx.send(f"<@{ctx.author.id}>'s hair length is now cleared.")

    @commandsplus.command(
        usage = "<length>"
    )
    @commands.guild_only()
    async def settail(self, ctx, *, newtail):
        """Set a custom tail length."""
        newtailsv = SV.parse(newtail)

        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.taillength = newtailsv
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name})'s tail is now {userdata.taillength:m} long.")
        await ctx.send(f"<@{ctx.author.id}>'s tail is now {userdata.taillength:mu} long.")

    @commandsplus.command(
        aliases = ["cleartail", "unsettail"]
    )
    @commands.guild_only()
    async def resettail(self, ctx):
        """Remove custom tail length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        userdata.taillength = None
        userdb.save(userdata)

        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) removed their custom tail length.")
        await ctx.send(f"<@{ctx.author.id}>'s tail length is now cleared.")

    @commandsplus.command(
        usage = "<male/female/none>"
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

    @commandsplus.command(
        aliases = ["cleargender", "unsetgender"]
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
