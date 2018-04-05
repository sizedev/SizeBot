import discord
from discord.ext import commands
from globalsb import *

class SetCog:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def changenick(self, ctx, newnick = None):
    #Change nickname.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot. 
    To register, use the `&register` command.""", delete_after=5)
        elif newnick is None:
            await ctx.send("Please enter `&changenick <newnick>`.", delete_after=3)
        else:
            userarray = read_user(ctx.message.author.id)
            userarray[NICK] = newnick + newline
            write_user(ctx.message.author.id, userarray)
            userarray = read_user(ctx.message.author.id)
            print (userarray)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx, userarray)

    @commands.command()
    async def setspecies(self, ctx, newtag = None):
    #Change nickname.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot. 
    To register, use the `&register` command.""", delete_after=5)
        elif newtag is None:
            await ctx.send("Please enter `&setspecies <newtag>`.", delete_after=3)
        else:
            userarray = read_user(ctx.message.author.id)
            userarray[SPEC] = newtag + newline
            write_user(ctx.message.author.id, userarray)
            userarray = read_user(ctx.message.author.id)
            print (userarray)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx, userarray)
            await ctx.send("""<@{0}> is now a {1}.""".format(ctx.message.author.id, userarray[SPEC]))

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
            print (userarray)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx, userarray)

    @commands.command()
    async def setheight(self, ctx, newheight = None):
        await ctx.message.delete()
        #Change height.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot. 
    To register, use the `&register` command.""", delete_after=5)
        elif newheight is None:
            await ctx.send("Please enter `&setheight <height>`.", delete_after=3)
        else:
            userarray = read_user(ctx.message.author.id)
            userarray[CHEI] = str(toSV(getnum(newheight), getlet(newheight))) + newline
            if (float(userarray[CHEI]) > infinity):
                print(warn("Invalid size value."))
                await ctx.send("Too big. x_x", delete_after=3)
                userarray[CHEI] = str(infinity) + newline
            write_user(ctx.message.author.id, userarray)
            userarray = read_user(ctx.message.author.id)
            print (userarray)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx, userarray)
            await ctx.send("""<@{0}> is now {1} tall. ({2})""".format(ctx.message.author.id, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])))

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
            userarray = read_user(ctx.message.author.id)
            print (userarray)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx, userarray)

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
            print (userarray)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx, userarray)
            await ctx.send("""<@{0}> is now {1}x density.""".format(ctx.message.author.id, userarray[DENS][:-1]))

    @commands.command()
    async def setdisplay(self, ctx, newdisp = None):
        #Change height.
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
            print (userarray)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx, userarray)

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
            newheightminval = toSV(getnum(newheightmin), getlet(newheightmin))
            newheightmaxval = toSV(getnum(newheightmax), getlet(newheightmax))
            newheight = random.randint(newheightminval, newheightmaxval)
            userarray = read_user(ctx.message.author.id)
            userarray[CHEI] = str(newheight) + newline
            if (float(userarray[CHEI]) > infinity):
                print(warn("Invalid size value."))
                await ctx.send("Too big. x_x", delete_after=3)
                userarray[CHEI] = str(infinity) + newline
            write_user(ctx.message.author.id, userarray)
            userarray = read_user(ctx.message.author.id)
            print (userarray)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx, userarray)
            await ctx.send("""<@{0}> is now {1} tall. ({2})""".format(ctx.message.author.id, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])))

    @commands.command()
    async def setinf(self, ctx):
        userarray = read_user(ctx.message.author.id)
        await ctx.send("<@{0}> is now infinitely tall.".format(ctx.message.author.id), delete_after=3)
        userarray[CHEI] = str(infinity) + newline
        write_user(ctx.message.author.id, userarray)
        if userarray[DISP] == "Y\n":
            await nickupdate(ctx, userarray)

    @commands.command()
    async def set0(self, ctx):
        userarray = read_user(ctx.message.author.id)
        await ctx.send("<@{0}> is now nothing.".format(ctx.message.author.id), delete_after=3)
        userarray[CHEI] = "0" + newline
        write_user(ctx.message.author.id, userarray)
        if userarray[DISP] == "Y\n":
            await nickupdate(ctx, userarray)

    @commands.command()
    async def setbaseheight(self, ctx, newbaseheight = None):
        await ctx.message.delete()
        #Change base height.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot. 
    To register, use the `&register` command.""", delete_after=5)
        elif newbaseheight is None:
            await ctx.send("Please enter `&setbaseheight <height>`.", delete_after=3)
        else:
            userarray = read_user(ctx.message.author.id)
            userarray[BHEI] = str(toSV(getnum(newbaseheight), getlet(newbaseheight))) + newline
            write_user(ctx.message.author.id, userarray)
            userarray = read_user(ctx.message.author.id)
            print (userarray)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx, userarray)
            await ctx.send("""<@{0}>'s base height is now {1}. ({2})""".format(ctx.message.author.id, fromSV(userarray[BHEI]), fromSVUSA(userarray[BHEI])))

    @commands.command()
    async def setbaseweight(self, ctx, newbaseweight = None):
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
            userarray[BWEI] = str(toSV(getnum(newbaseweight), getlet(newbaseweight))) + newline
            write_user(ctx.message.author.id, userarray)
            userarray = read_user(ctx.message.author.id)
            print (userarray)
            if userarray[DISP] == "Y\n":
                await nickupdate(ctx, userarray)
            await ctx.send("""<@{0}>'s base weight is now {1}. ({2})""".format(ctx.message.author.id, fromWV(userarray[BWEI]), fromWVUSA(userarray[BWEI])))

#Necessary.
def setup(bot):
    bot.add_cog(SetCog(bot))