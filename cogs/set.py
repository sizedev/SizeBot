import discord
from discord.ext import commands
from globalsb import *
import digilogger as logger


def clamp(minVal, val, maxVal):
    return max(minVal, min(val, maxVal))


def requireUser(fn):
    async def wrapper(self, ctx, *args, **kwargs):
        # Change height
        if not os.path.exists(f"{folder}/users/{ctx.message.author.id}.txt"):
            # User file missing
            await ctx.send("Sorry! You aren't registered with SizeBot.\n"
                           "To register, use the `&register` command.", delete_after=5)
            return
        return await fn(self, ctx, *args, **kwargs)
    return wrapper


class SetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def changenick(self, ctx, *, newnick=None):
        # Change nickname.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
            # User file missing.
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
    async def setspecies(self, ctx, *, newtag=None):
        # Change nickname.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
            # User file missing.
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
        # Change nickname.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
            # User file missing.
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
    async def setheight(self, ctx, *, newheight=None):
        # Change height.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
            # User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot.
    To register, use the `&register` command.""", delete_after=5)
        elif newheight is None:
            await ctx.send("Please enter `&setheight <height>`.", delete_after=3)
        else:
            newheight = isFeetAndInchesAndIfSoFixIt(newheight)
            userarray = read_user(ctx.message.author.id)
            userarray[CHEI] = str(toSV(getnum(newheight), getlet(newheight))) + newline
            try:
                if (float(userarray[CHEI]) > infinity):
                    logger.warn("Invalid size value.")
                    await ctx.send("Too big. x_x", delete_after=3)
                    userarray[CHEI] = str(infinity) + newline
            except Exception as e:
                df.crit(e)
                await ctx.send(f"<@{digiid}> CRITICAL ERROR\n{ctx.message.author.id}\n{e}")
            write_user(ctx.message.author.id, userarray)
            userarray = read_user(ctx.message.author.id)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx.message.author)
            logger.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) is now {str(newheight)} tall.")
            await ctx.send("""<@{0}> is now {1} tall. ({2})""".format(ctx.message.author.id, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])))

    @commands.command()
    async def resetsize(ctx):
        # Change nickname.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
            # User file missing.
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
    async def setdensity(self, ctx, newdensity: float = None):
        await ctx.message.delete()
        # Change density.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
            # User file missing.
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
    async def setdisplay(self, ctx, newdisp=None):
        # Set display mode.
        newdisp = newdisp.upper()
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
            # User file missing.
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
            await ctx.send("""<@{0}>'s display is now set to {1}.""".format(ctx.message.author.id, userarray[DISP][:-1]))

    @commands.command()
    async def setsystem(self, ctx, newsys=None):
        # Set measurement system.
        newsys = newsys.upper()
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
            # User file missing.
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

    @commands.command("setrandomheight")
    @requireUser
    async def setrandomheight(self, ctx, minheightstr, maxheightstr):
        # Parse min and max heights
        minheightstr = isFeetAndInchesAndIfSoFixIt(minheightstr)
        maxheightstr = isFeetAndInchesAndIfSoFixIt(maxheightstr)
        minheightSV = toSV(getnum(minheightstr), getlet(minheightstr))
        maxheightSV = toSV(getnum(maxheightstr), getlet(maxheightstr))

        # Clamp min and max heights to acceptable values
        minheightSV = clamp(0, minheightSV, infinity)
        maxheightSV = clamp(0, maxheightSV, infinity)

        # Swap values if provided in the wrong order
        if minheightSV > maxheightSV:
            minheightSV, maxheightSV = maxheightSV, minheightSV

        precision = Decimal("1E26")

        minheightlog = minheightSV.log10()
        maxheightlog = maxheightSV.log10()

        minheightintlog = (minheightlog * precision).to_integral_value()
        maxheightintlog = (maxheightlog * precision).to_integral_value()

        newheightintlog = Decimal(random.randint(minheightintlog, maxheightintlog))

        newheightlog = newheightintlog / precision

        newheight = Decimal("10") ** newheightlog

        userarray = read_user(ctx.message.author.id)
        userarray[CHEI] = f"{newheight}\n"
        write_user(ctx.message.author.id, userarray)

        if userarray[DISP].rstrip().upper() == "Y":
            await nickupdate(ctx.message.author)

        logger.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) set a random height, and are now {newheight}SV tall.")
        await ctx.send(f"<@{ctx.message.author.id}> is now {fromSV(userarray[CHEI])} tall. ({fromSVUSA(userarray[CHEI])})")

    @setrandomheight.error
    async def setrandomheight_handler(self, ctx, error):
        # Check if required argument is missing
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please enter `&setrandomheight [minheight] [maxheight]`.", delete_after=3)
            return
        raise error

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
    async def setbaseheight(self, ctx, *, newbaseheight=None):
        # Change base height.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
            # User file missing.
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
    async def setbaseweight(self, ctx, *, newbaseweight=None):
        await ctx.message.delete()
        # Change base weight.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
            # User file missing.
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


# Necessary.
def setup(bot):
    bot.add_cog(SetCog(bot))
