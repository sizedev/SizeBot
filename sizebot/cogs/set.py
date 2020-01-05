import random

from discord.ext import commands

from sizebot import digilogger as logger
from sizebot import userdb
from sizebot import digiSV
from sizebot import digisize
from sizebot.checks import guildOnly


class SetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Change nickname
    @commands.command()
    @commands.check(guildOnly)
    async def changenick(self, ctx, *, newnick = None):
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newnick is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <newnick>`.")
            return

        userdata = userdb.load(ctx.message.author.id)

        userdata.nickname = newnick
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) changed their nick to {str(newnick)}.")
        await ctx.send(f"<@{ctx.message.author.id}>'s nick is now {userdata.nickname}")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    # Change species
    @commands.command()
    @commands.check(guildOnly)
    async def setspecies(self, ctx, *, newtag = None):
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newtag is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <newtag>`.")
            return

        userdata = userdb.load(ctx.message.author.id)

        userdata.species = newtag
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) changed their species to {str(newtag)}.")
        await ctx.send("<@{ctx.message.author.id}>'s species is now {userdata.species}")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    # Remove species
    @commands.command()
    @commands.check(guildOnly)
    async def clearspecies(self, ctx):
        userdata = userdb.load(ctx.message.author.id)

        userdata.species = None
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) removed their species.")
        await ctx.send("<@{ctx.message.author.id}>'s species is now cleared")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    # Change height
    @commands.command()
    @commands.check(guildOnly)
    async def setheight(self, ctx, *, newheight = None):
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newheight is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <height>`.")
            return

        newheightsv = digiSV.toSV(newheight)
        if newheightsv > digiSV.infinity:
            await logger.warn("Invalid size value.")
            await ctx.send("Too big. x_x")
            newheightsv = digiSV.infinitySV

        userdata = userdb.load(ctx.message.author.id)

        userdata.height = newheightsv
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) is now {str(newheight)} tall.")
        await ctx.send(f"<@{ctx.message.author.id}> is now {digiSV.fromSV(userdata.height, 'm')} tall. ({digiSV.fromSV(userdata.height, 'u')})")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    # Reset size
    @commands.command()
    @commands.check(guildOnly)
    async def resetsize(self, ctx):
        userdata = userdb.load(ctx.message.author.id)

        userdata.height = userdata.baseheight
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) reset their size.")
        # TODO: Add user message

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    # Set display mode
    @commands.command()
    @commands.check(guildOnly)
    async def setdisplay(self, ctx, newdisp = None):
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

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) set their display to {str(newdisp)}.")
        await ctx.send(f"<@{ctx.message.author.id}>'s display is now set to {userdata.display}.")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    # Set measurement system
    @commands.command()
    @commands.check(guildOnly)
    async def setsystem(self, ctx, newsys = None):
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

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) set their system to {str(newsys)}.")
        await ctx.send(f"<@{ctx.message.author.id}>'s system is now set to {userdata.unitsystem}.'")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    # Change height to a random value
    @commands.command()
    @commands.check(guildOnly)
    async def setrandomheight(self, ctx, newheightmin = None, newheightmax = None):
        if newheightmin is None or newheightmax is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <height>`.")
            return

        newheightminSV = digiSV.toSV(newheightmin)
        newheightmaxSV = digiSV.toSV(newheightmax)
        newheight = random.randint(newheightminSV, newheightmaxSV)
        if newheight > digiSV.infinity:
            await logger.warn("Invalid size value.")
            await ctx.send("Too big. x_x")
            newheight = digiSV.infinitySV

        userdata = userdb.load(ctx.message.author.id)

        userdata.height = newheight
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) set a random height, and are now {str(newheight)}SV tall.")
        await ctx.send(f"<@{ctx.message.author.id}> is now {digiSV.fromSV(userdata.height, 'm')} tall. ({digiSV.fromSV(userdata.height, 'u')})")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    # Change height to a infinity
    @commands.command()
    @commands.check(guildOnly)
    async def setinf(self, ctx):
        userdata = userdb.load(ctx.message.author.id)

        userdata.height = digiSV.infinitySV
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) is now infinitely tall.")
        await ctx.send(f"<@{ctx.message.author.id}> is now infinitely tall.")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    # Change height to a zero
    @commands.command()
    @commands.check(guildOnly)
    async def set0(self, ctx):
        userdata = userdb.load(ctx.message.author.id)

        userdata.height = 0
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) is now nothing.")
        await ctx.send(f"<@{ctx.message.author.id}> is now nothing.")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    # Change base height
    @commands.command()
    @commands.check(guildOnly)
    async def setbaseheight(self, ctx, *, newbaseheight = None):
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newbaseheight is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <height>`.")
            return

        userdata = userdb.load(ctx.message.author.id)

        userdata.baseheight = digiSV.toSV(newbaseheight)
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) changed their base height to {str(newbaseheight)}.")
        await ctx.send(f"<@{ctx.message.author.id}>'s base height is now {digiSV.fromSV(userdata.baseheight, 'm')}. ({digiSV.fromSV(userdata.baseheight, 'u')})")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)

    # Change base weight
    @commands.command()
    @commands.check(guildOnly)
    async def setbaseweight(self, ctx, *, newbaseweight = None):
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newbaseweight is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <weight>`.")
            return

        userdata = userdb.load(ctx.message.author.id)

        userdata.baseweight = digiSV.toWV(newbaseweight)
        userdb.save(userdata)

        await logger.info(f"User {ctx.message.author.id} ({ctx.message.author.display_name}) changed their base weight to {str(newbaseweight)}.")
        await ctx.send(f"<@{ctx.message.author.id}>'s base weight is now {digiSV.fromWV(userdata.baseweight, 'm')}. ({digiSV.fromWV(userdata.baseweight, 'u')})")

        if userdata.display:
            await digisize.nickUpdate(ctx.message.author)


# Necessary
def setup(bot):
    bot.add_cog(SetCog(bot))
