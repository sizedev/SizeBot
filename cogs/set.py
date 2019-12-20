import random

from discord.ext import commands

import digiformatter as df
import userdb
from userdb import NICK, DISP, SPEC, CHEI, BHEI, DENS, UNIT, BWEI
import digiSV
import digisize


class SetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Change nickname
    @commands.command()
    async def changenick(self, ctx, *, newnick = None):
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newnick is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <newnick>`.")
            return

        userdata = userdb.load(ctx.message.author.id)

        userdata.nickname = newnick
        userdb.save(userdata)

        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) changed their nick to {str(newnick)}.")
        await ctx.send("<@{0}>'s nick is now {1}".format(ctx.message.author.id, userdata[NICK]))

        if userdata[DISP]:
            await digisize.nickUpdate(ctx.message.author)

    # Change species
    @commands.command()
    async def setspecies(self, ctx, *, newtag = None):
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newtag is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <newtag>`.")
            return

        userdata = userdb.load(ctx.message.author.id)

        userdata.species = newtag
        userdb.save(userdata)

        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) changed their species to {str(newtag)}.")
        await ctx.send("<@{0}>'s species is now {1}".format(ctx.message.author.id, userdata[SPEC]))

        if userdata[DISP]:
            await digisize.nickUpdate(ctx.message.author)

    # Remove species
    @commands.command()
    async def clearspecies(self, ctx):
        userdata = userdb.load(ctx.message.author.id)

        userdata[SPEC] = None
        userdb.save(userdata)

        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) removed their species.")
        await ctx.send("<@{0}>'s species is now cleared".format(ctx.message.author.id))

        if userdata[DISP]:
            await digisize.nickUpdate(ctx.message.author)

    # Change height
    @commands.command()
    async def setheight(self, ctx, *, newheight = None):
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newheight is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <height>`.")
            return

        newheightsv = digiSV.toSV(newheight)
        if newheightsv > digiSV.infinity:
            df.warn("Invalid size value.")
            await ctx.send("Too big. x_x")
            newheightsv = digiSV.infinity

        userdata = userdb.load(ctx.message.author.id)

        userdata.height = newheightsv
        userdb.save(userdata)

        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) is now {str(newheight)} tall.")
        await ctx.send(f"<@{ctx.message.author.id}> is now {digiSV.fromSV(userdata[CHEI], 'm')} tall. ({digiSV.fromSV(userdata[CHEI], 'u')})")

        if userdata[DISP]:
            await digisize.nickUpdate(ctx.message.author)

    # Reset size
    @commands.command()
    async def resetsize(self, ctx):
        userdata = userdb.load(ctx.message.author.id)

        userdata[CHEI] = userdata[BHEI]
        userdb.save(userdata)

        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) reset their size.")
        # TODO: Add user message

        if userdata[DISP]:
            await digisize.nickUpdate(ctx.message.author)

    # Change density
    @commands.command()
    async def setdensity(self, ctx, newdensity: float = None):
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newdensity is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <density>`.")
            return

        userdata = userdb.load(ctx.message.author.id)

        userdata[DENS] = newdensity
        userdb.save(userdata)

        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) is now {str(newdensity)}x density.")
        await ctx.send("""<@{0}> is now {1}x density.""".format(ctx.message.author.id, userdata[DENS][:-1]))

        if userdata[DISP]:
            await digisize.nickUpdate(ctx.message.author)

    # Set display mode
    @commands.command()
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

        userdata[DISP] = newdisp
        userdb.save(userdata)

        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) set their display to {str(newdisp)}.")
        await ctx.send("""<@{0}>'s display is now set to {1}.""".format(ctx.message.author.id, userdata[DISP][:-1]))

        if userdata[DISP]:
            await digisize.nickUpdate(ctx.message.author)

    # Set measurement system
    @commands.command()
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

        userdata[UNIT] = newsys
        userdb.save(userdata)

        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) set their system to {str(newsys)}.")
        await ctx.send("""<@{0}>'s system is now set to {1}.'""".format(ctx.message.author.id, userdata[UNIT][:-1]))

        if userdata[DISP]:
            await digisize.nickUpdate(ctx.message.author)

    # Change height to a random value
    @commands.command()
    async def setrandomheight(self, ctx, newheightmin = None, newheightmax = None):
        if newheightmin is None or newheightmax is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <height>`.")
            return

        newheightminSV = digiSV.toSV(newheightmin)
        newheightmaxSV = digiSV.toSV(newheightmax)
        newheight = random.randint(newheightminSV, newheightmaxSV)
        if newheight > digiSV.infinity:
            df.warn("Invalid size value.")
            await ctx.send("Too big. x_x")
            newheight = digiSV.infinity

        userdata = userdb.load(ctx.message.author.id)

        userdata[CHEI] = newheight
        userdb.save(userdata)

        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) set a random height, and are now {str(newheight)}SV tall.")
        await ctx.send(f"<@{ctx.message.author.id}> is now {digiSV.fromSV(userdata[CHEI], 'm')} tall. ({digiSV.fromSV(userdata[CHEI], 'u')})")

        if userdata[DISP]:
            await digisize.nickUpdate(ctx.message.author)

    # Change height to a infinity
    @commands.command()
    async def setinf(self, ctx):
        userdata = userdb.load(ctx.message.author.id)

        userdata[CHEI] = digiSV.infinity
        userdb.save(userdata)

        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) is now infinitely tall.")
        await ctx.send("<@{0}> is now infinitely tall.".format(ctx.message.author.id))

        if userdata[DISP]:
            await digisize.nickUpdate(ctx.message.author)

    # Change height to a zero
    @commands.command()
    async def set0(self, ctx):
        userdata = userdb.load(ctx.message.author.id)

        userdata[CHEI] = 0
        userdb.save(userdata)

        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) is now nothing.")
        await ctx.send("<@{0}> is now nothing.".format(ctx.message.author.id))

        if userdata[DISP]:
            await digisize.nickUpdate(ctx.message.author)

    # Change base height
    @commands.command()
    async def setbaseheight(self, ctx, *, newbaseheight = None):
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newbaseheight is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <height>`.")
            return

        userdata = userdb.load(ctx.message.author.id)

        userdata[BHEI] = digiSV.toSV(newbaseheight)
        userdb.save(userdata)

        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) changed their base height to {str(newbaseheight)}.")
        await ctx.send(f"<@{ctx.message.author.id}>'s base height is now {digiSV.fromSV(userdata[BHEI], 'm')}. ({digiSV.fromSV(userdata[BHEI], 'u')})")

        if userdata[DISP]:
            await digisize.nickUpdate(ctx.message.author)

    # Change base weight
    @commands.command()
    async def setbaseweight(self, ctx, *, newbaseweight = None):
        # TODO: Move this to an error handler for MissingRequiredArgument
        if newbaseweight is None:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} <weight>`.")
            return

        userdata = userdb.load(ctx.message.author.id)

        userdata[BWEI] = digiSV.toWV(newbaseweight)
        userdb.save(userdata)

        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) changed their base weight to {str(newbaseweight)}.")
        await ctx.send(f"<@{ctx.message.author.id}>'s base weight is now {digiSV.fromWV(userdata[BWEI], 'm')}. ({digiSV.fromWV(userdata[BWEI], 'u')})")

        if userdata[DISP]:
            await digisize.nickUpdate(ctx.message.author)


# Necessary
def setup(bot):
    bot.add_cog(SetCog(bot))
