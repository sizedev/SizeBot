import discord
from discord.ext import commands
from globalsb import *
import digilogger as logger

class SetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def changenick(self, ctx, *, newnick = None):
    #Change nickname.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot.
    To register, use the `&register` command.""", delete_after=5)
        elif newnick is None:
            await ctx.send("Please enter `&changenick <newnick>`.", delete_after=3)
        else:
            userarray = read_user(ctx.message.author.id)
            olduserarray = userarray
            userarray[NICK] = newnick + newline
            try:
                write_user(ctx.message.author.id, userarray)
                userarray = read_user(ctx.message.author.id)
                await ctx.send("<@{0}>'s nick is now {1}".format(ctx.message.author.id, userarray[NICK]))
            except():
                userarray = olduserarray
                await ctx.send("<@{0}> Unicode error! Please don't put Unicode characters in your nick.".format(ctx.message.author.id))
            logger.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) changed their nick to {str(newnick)}.")
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx.message.author)

    @commands.command()
    async def setspecies(self, ctx, *, newtag = None):
    #Change nickname.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot.
    To register, use the `&register` command.""", delete_after=5)
        elif newtag is None:
            await ctx.send("Please enter `&setspecies <newtag>`.", delete_after=3)
        else:
            userarray = read_user(ctx.message.author.id)
            olduserarray = userarray
            userarray[SPEC] = newtag + newline
            try:
                write_user(ctx.message.author.id, userarray)
                userarray = read_user(ctx.message.author.id)
                await ctx.send("<@{0}>'s species is now {1}".format(ctx.message.author.id, userarray[SPEC]))
            except():
                userarray = olduserarray
                await ctx.send("<@{0}> Unicode error! Please don't put Unicode characters in your species.".format(ctx.message.author.id))
            logger.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) changed their species to {str(newtag)}.")
            userarray = read_user(ctx.message.author.id)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx.message.author)

    @commands.command()
    async def clearspecies(self, ctx):
    #Change nickname.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot.
    To register, use the `&register` command.""", delete_after=5)
        else:
            userarray = read_user(ctx.message.author.id)
            userarray[SPEC] = "None" + newline
            write_user(ctx.message.author.id, userarray)
            userarray = read_user(ctx.message.author.id)
            logger.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) removed their species.")
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx.message.author)

    @commands.command()
    async def setheight(self, ctx, *, newheight = None):
        #Change height.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot.
    To register, use the `&register` command.""", delete_after=5)
        elif newheight is None:
            await ctx.send("Please enter `&setheight <height>`.", delete_after=3)
        else:
            newheight = isFeetAndInchesAndIfSoFixIt(newheight)
            userarray = read_user(ctx.message.author.id)
            userarray[CHEI] = str(toSV(getnum(newheight), getlet(newheight))) + newline
            if (float(userarray[CHEI]) > infinity):
                logger.warn("Invalid size value.")
                await ctx.send("Too big. x_x", delete_after=3)
                userarray[CHEI] = str(infinity) + newline
            write_user(ctx.message.author.id, userarray)
            userarray = read_user(ctx.message.author.id)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx.message.author)
            logger.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) is now {str(newheight)} tall.")
            await ctx.send("""<@{0}> is now {1} tall. ({2})""".format(ctx.message.author.id, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])))

    @commands.command()
    async def resetsize(ctx):
    #Change nickname.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot.
    To register, use the `&register` command.""", delete_after=5)
        else:
            userarray = read_user(ctx.message.author.id)
            userarray[CHEI] = userarray[BHEI]
            write_user(ctx.message.author.id, userarray)
            logger.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) reset their size.")
            userarray = read_user(ctx.message.author.id)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx.message.author)

    @commands.command()
    async def setdensity(self, ctx, newdensity : float = None):
        await ctx.message.delete()
        #Change density.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot.
    To register, use the `&register` command.""", delete_after=5)
        elif newdensity is None:
            await ctx.send("Please enter `&setdensity <density>`.", delete_after=3)
        else:
            userarray = read_user(ctx.message.author.id)
            userarray[DENS] = str(newdensity) + newline
            write_user(ctx.message.author.id, userarray)
            userarray = read_user(ctx.message.author.id)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx.message.author)
            logger.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) is now {str(newdensity)}x density.")
            await ctx.send("""<@{0}> is now {1}x density.""".format(ctx.message.author.id, userarray[DENS][:-1]))

    @commands.command()
    async def setdisplay(self, ctx, newdisp = None):
        #Set display mode.
        newdisp = newdisp.upper()
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot.
    To register, use the `&register` command.""", delete_after=5)
        elif newdisp not in ["Y", "N"]:
            await ctx.send("Please enter `&setdisplay [Y/N]`.", delete_after=3)
        else:
            userarray = read_user(ctx.message.author.id)
            userarray[DISP] = str(newdisp) + newline
            write_user(ctx.message.author.id, userarray)
            userarray = read_user(ctx.message.author.id)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx.message.author)
            logger.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) set their display to {str(newdisp)}.")
            await ctx.send("""<@{0}>'s display is now set to {1}.'""".format(ctx.message.author.id, userarray[DISP][:-1]))

    @commands.command()
    async def setsystem(self, ctx, newsys = None):
        #Set measurement system.
        newsys = newsys.upper()
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot.
    To register, use the `&register` command.""", delete_after=5)
        elif newsys not in ["M", "U"]:
            await ctx.send("Please enter `&setsystem [U/M]`.", delete_after=3)
        else:
            userarray = read_user(ctx.message.author.id)
            userarray[UNIT] = str(newsys) + newline
            write_user(ctx.message.author.id, userarray)
            userarray = read_user(ctx.message.author.id)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx.message.author)
            logger.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) set their system to {str(newsys)}.")
            await ctx.send("""<@{0}>'s system is now set to {1}.'""".format(ctx.message.author.id, userarray[UNIT][:-1]))

    @commands.command()
    async def setrandomheight(self, ctx, newheightmin = None, newheightmax = None):
        #Change height.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot.
    To register, use the `&register` command.""", delete_after=5)
        elif newheightmin is None or newheightmax is None:
            await ctx.send("Please enter `&setheight <height>`.", delete_after=3)
        else:
            newheightmin = isFeetAndInchesAndIfSoFixIt(newheightmin)
            newheightmax = isFeetAndInchesAndIfSoFixIt(newheightmax)
            newheightminval = toSV(getnum(newheightmin), getlet(newheightmin))
            newheightmaxval = toSV(getnum(newheightmax), getlet(newheightmax))
            newheight = random.randint(newheightminval, newheightmaxval)
            userarray = read_user(ctx.message.author.id)
            userarray[CHEI] = str(newheight) + newline
            if (float(userarray[CHEI]) > infinity):
                logger.warn("Invalid size value.")
                await ctx.send("Too big. x_x", delete_after=3)
                userarray[CHEI] = str(infinity) + newline
            write_user(ctx.message.author.id, userarray)
            userarray = read_user(ctx.message.author.id)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx.message.author)
            logger.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) set a random height, and are now {str(newheight)}SV tall.")
            await ctx.send("""<@{0}> is now {1} tall. ({2})""".format(ctx.message.author.id, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])))

    @commands.command()
    async def setinf(self, ctx):
        userarray = read_user(ctx.message.author.id)
        await ctx.send("<@{0}> is now infinitely tall.".format(ctx.message.author.id))
        userarray[CHEI] = str(infinity) + newline
        write_user(ctx.message.author.id, userarray)
        logger.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) is now infinitely tall.")
        if userarray[DISP] == "Y\n":
            await nickupdate(ctx.message.author)

    @commands.command()
    async def set0(self, ctx):
        userarray = read_user(ctx.message.author.id)
        await ctx.send("<@{0}> is now nothing.".format(ctx.message.author.id))
        userarray[CHEI] = "0" + newline
        write_user(ctx.message.author.id, userarray)
        logger.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) is now nothing.")
        if userarray[DISP] == "Y\n":
            await nickupdate(ctx.message.author)

    @commands.command()
    async def setbaseheight(self, ctx, *, newbaseheight = None):
        #Change base height.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot.
    To register, use the `&register` command.""", delete_after=5)
        elif newbaseheight is None:
            await ctx.send("Please enter `&setbaseheight <height>`.", delete_after=3)
        else:
            newbaseheight = isFeetAndInchesAndIfSoFixIt(newbaseheight)
            userarray = read_user(ctx.message.author.id)
            userarray[BHEI] = str(toSV(getnum(newbaseheight), getlet(newbaseheight))) + newline
            write_user(ctx.message.author.id, userarray)
            userarray = read_user(ctx.message.author.id)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx.message.author)
            logger.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) changed their base height to {str(newbaseheight)}.")
            await ctx.send("""<@{0}>'s base height is now {1}. ({2})""".format(ctx.message.author.id, fromSV(userarray[BHEI]), fromSVUSA(userarray[BHEI])))

    @commands.command()
    async def setbaseweight(self, ctx, *, newbaseweight = None):
        await ctx.message.delete()
        #Change base weight.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot.
    To register, use the `&register` command.""", delete_after=5)
        elif newbaseweight is None:
            await ctx.send("Please enter `&setbaseweight <weight>`.", delete_after=3)
        else:
            userarray = read_user(ctx.message.author.id)
            userarray[BWEI] = str(toWV(getnum(newbaseweight), getlet(newbaseweight))) + newline
            write_user(ctx.message.author.id, userarray)
            userarray = read_user(ctx.message.author.id)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx.message.author)
            logger.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) changed their base weight to {str(newbaseweight)}.")
            await ctx.send("""<@{0}>'s base weight is now {1}. ({2})""".format(ctx.message.author.id, fromWV(userarray[BWEI]), fromWVUSA(userarray[BWEI])))

#Necessary.
def setup(bot):
    bot.add_cog(SetCog(bot))
