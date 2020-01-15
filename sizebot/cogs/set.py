from discord.ext import commands
from sizebot.discordplus import commandsplus

from sizebot import digilogger as logger
from sizebot import userdb
from sizebot.digiSV import SV, WV
from sizebot import digisize
from sizebot.utils import clamp
import sizebot.digidecimal as digidecimal
from sizebot import digierror as errors


class SetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commandsplus.command(
        aliases = ["changenick", "nick"],
        usage = "<nick>"
    )
    @commands.guild_only()
    async def setnick(self, ctx, *, newnick = None):
        """Change nickname."""
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newnick is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <newnick>`.")
            return

        userdata = userdb.load(ctx.message.author.id)

        userdata.nickname = newnick
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) changed their nick to {userdata.nickname}.")
        await ctx.send(f"<@{ctx.message.author.id}>'s nick is now {userdata.nickname}")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    @commandsplus.command(
        usage = "<species>"
    )
    @commands.guild_only()
    async def setspecies(self, ctx, *, newtag = None):
        """Change species."""
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newtag is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <newtag>`.")
            return

        userdata = userdb.load(ctx.message.author.id)

        userdata.species = newtag
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) changed their species to {userdata.species}.")
        await ctx.send(f"<@{ctx.message.author.id}>'s species is now {userdata.species}")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    @commandsplus.command()
    @commands.guild_only()
    async def clearspecies(self, ctx):
        """Remove species."""
        userdata = userdb.load(ctx.message.author.id)

        userdata.species = None
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) removed their species.")
        await ctx.send("<@{ctx.message.author.id}>'s species is now cleared")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    @commandsplus.command(
        usage = "<height>"
    )
    @commands.guild_only()
    async def setheight(self, ctx, *, newheight = None):
        """Change height."""
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newheight is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <height>`.")
            return

        newheightsv = SV.parse(newheight)
        if newheightsv > SV.infinity:
            await logger.warn("Invalid size value.")
            await ctx.send("Too big. x_x")
            newheightsv = SV.infinity

        userdata = userdb.load(ctx.message.author.id)

        userdata.height = newheightsv
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) is now {userdata.height:m} tall.")
        await ctx.send(f"<@{ctx.message.author.id}> is now {userdata.height:m} tall. ({userdata.height:u})")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    @commandsplus.command(
        aliases = ["resetheight", "reset"]
    )
    @commands.guild_only()
    async def resetsize(self, ctx):
        """Reset size."""
        userdata = userdb.load(ctx.message.author.id)

        userdata.height = userdata.baseheight
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) reset their size.")
        # TODO: Add user message

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    @commandsplus.command(
        usage = "<Y/N>"
    )
    @commands.guild_only()
    async def setdisplay(self, ctx, newdisp = None):
        """Set display mode."""
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newdisp is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} [Y/N]`.")
            return

        newdisp = newdisp.upper()
        if newdisp not in ["Y", "N"]:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} [Y/N]`.")
            return

        userdata = userdb.load(ctx.message.author.id)

        userdata.display = newdisp
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) set their display to {newdisp}.")
        await ctx.send(f"<@{ctx.message.author.id}>'s display is now set to {userdata.display}.")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    @commandsplus.command(
        usage = "<M/U>"
    )
    @commands.guild_only()
    async def setsystem(self, ctx, newsys = None):
        """Set measurement system."""
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newsys is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} [u/m]`.")
            return

        newsys = newsys.lower()
        if newsys not in ["m", "u"]:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} [u/m]`.")
            return

        userdata = userdb.load(ctx.message.author.id)

        userdata.unitsystem = newsys
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) set their system to {userdata.unitsystem}.")
        await ctx.send(f"<@{ctx.message.author.id}>'s system is now set to {userdata.unitsystem}.'")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    @commandsplus.command(
        usage = "<minheight> <maxheight>"
    )
    @commands.guild_only()
    async def setrandomheight(self, ctx, minheight = None, maxheight = None):
        """Change height to a random value.

        Sets your height to a height between `minheight` and `maxheight`.
        Weighted on a logarithmic curve."""
        # TODO: Move this to an error handler for MissingRequiredArgument
        if minheight is None or maxheight is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <height>`.")
            return

        minheightSV = clamp(0, SV.parse(minheight), SV.infinity)
        maxheightSV = clamp(0, SV.parse(maxheight), SV.infinity)

        newheightSV = digidecimal.randRangeLog(minheightSV, maxheightSV)

        userdata = userdb.load(ctx.message.author.id)

        userdata.height = newheightSV
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) set a random height, and are now {userdata.height:m} tall.")
        await ctx.send(f"<@{ctx.message.author.id}> is now {userdata.height:m} tall. ({userdata.height:u})")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    @commandsplus.command()
    @commands.guild_only()
    async def setinf(self, ctx):
        """Change height to infinity."""
        userdata = userdb.load(ctx.message.author.id)

        userdata.height = SV.infinity
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) is now infinitely tall.")
        await ctx.send(f"<@{ctx.message.author.id}> is now infinitely tall.")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    @commandsplus.command()
    @commands.guild_only()
    async def set0(self, ctx):
        """Change height to a zero."""
        userdata = userdb.load(ctx.message.author.id)

        userdata.height = 0
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) is now nothing.")
        await ctx.send(f"<@{ctx.message.author.id}> is now nothing.")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    @commandsplus.command(
        usage = "<height>"
    )
    @commands.guild_only()
    async def setbaseheight(self, ctx, *, newbaseheight = None):
        """Change base height."""
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newbaseheight is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <height>`.")
            return

        userdata = userdb.load(ctx.message.author.id)

        userdata.baseheight = SV.parse(newbaseheight)
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) changed their base height to {newbaseheight}.")
        await ctx.send(f"<@{ctx.message.author.id}>'s base height is now {userdata.baseheight:m}. ({userdata.baseheight:u})")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    @commandsplus.command(
        usage = "<weight>"
    )
    @commands.guild_only()
    async def setbaseweight(self, ctx, *, newbaseweight = None):
        """Change base weight."""
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newbaseweight is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <weight>`.")
            return

        userdata = userdb.load(ctx.message.author.id)

        userdata.baseweight = WV.parse(newbaseweight)
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) changed their base weight to {newbaseweight}.")
        await ctx.send(f"<@{ctx.message.author.id}>'s base weight is now {userdata.baseweight:m}. ({userdata.baseweight:u})")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    # TODO: Make this accept shoe size as an input.
    @commandsplus.command(
        usage = "<length>"
    )
    @commands.guild_only()
    async def setfoot(self, ctx, *, newfoot = None):
        """Change custom foot length."""
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newfoot is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} [length]`.")
            return

        newfootsv = SV.parse(newfoot)
        if newfootsv > SV.infinity:
            await logger.warn("Invalid size value.")
            await ctx.send("Too big. x_x")
            newfootsv = SV.infinity

        userdata = userdb.load(ctx.message.author.id)

        userdata.footlength = newfootsv
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name})'s foot is now {userdata.footlength:m} long.")
        await ctx.send(f"<@{ctx.message.author.id}>'s foot is now {userdata.footlength:mu} long.")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    @commandsplus.command(
        aliases = ["clearfoot", "unsetfoot"]
    )
    @commands.guild_only()
    async def resetfoot(self, ctx):
        """Remove custom foot length."""
        userdata = userdb.load(ctx.message.author.id)

        userdata.footlength = None
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) removed their custom foot length.")
        await ctx.send("<@{ctx.message.author.id}>'s foot length is now default.")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    @commandsplus.command(
        usage = "<male/female/none>"
    )
    @commands.guild_only()
    async def setgender(self, ctx, gender):
        """Set gender."""

        user = ctx.author

        gendermap = {
            "m": "m",
            "male": "m",
            "man": "m",
            "boy": "m",
            "f": "f",
            "female": "f",
            "woman": "f",
            "girl": "f",
            "none": None,
            None: None
        }
        try:
            gender = gendermap[gender]
        except KeyError:
            raise errors.ArgumentException(ctx)

        userdata = userdb.load(user.id)
        userdata.gender = gender
        userdb.save(userdata)

        if userdata.display:
            await digisize.nickUpdate(user)

        await logger.info(f"User {user.id} ({user.display_name}) set their gender to {userdata.gender}.")
        await ctx.send(f"<@{user.id}>'s gender is now set to {userdata.gender}.")

    @setgender.error
    async def setgender_handler(self, ctx, error):
        # Check if required argument is missing
        if isinstance(error, commands.MissingRequiredArgument):
            raise errors.ArgumentException(ctx)
        raise error

    @commandsplus.command(
        aliases = ["cleargender", "unsetgender"]
    )
    @commands.guild_only()
    async def resetgender(self, ctx):
        """Reset gender."""

        user = ctx.author

        userdata = userdb.load(user.id)
        userdata.gender = None
        userdb.save(userdata)

        if userdata.display:
            await digisize.nickUpdate(user)

        await logger.info(f"User {user.id} ({user.display_name}) reset their gender.")
        await ctx.send(f"<@{user.id}>'s gender is now reset.")


def setup(bot):
    bot.add_cog(SetCog(bot))
