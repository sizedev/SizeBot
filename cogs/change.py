import discord
from discord.ext import commands
from globalsb import *
import digiformatter as df

class ChangeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TODO: This isn't very clean.
    @commands.command()
    async def change(self, ctx, style, *, amount):
        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) changed {style}-style {amount}.")
        #Change height.
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot.
    To register, use the `&register` command.""", delete_after=5)
        elif style == "a" or style == "+" or style == "add":
            amount = isFeetAndInchesAndIfSoFixIt(amount)
            userarray = readUser(ctx.message.author.id)
            userarray[CHEI] = str(Decimal(userarray[CHEI]) + Decimal(toSV(getNum(amount), getLet(amount)))) + newline
            if (float(userarray[CHEI]) > infinity):
                df.warn("Invalid size value.")
                await ctx.send("Too big. x_x", delete_after=3)
                userarray[CHEI] = str(infinity) + newline
            writeUser(ctx.message.author.id, userarray)
            userarray = readUser(ctx.message.author.id)
            if userarray[DISP] == "Y\n":
                await nickUpdate(ctx.message.author)
            await ctx.send("""<@{0}> is now {1} tall. ({2})""".format(ctx.message.author.id, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI]))) #Add comp to base.
        elif style == "m" or style == "*" or style == "x" or style == "mult" or style == "multiply":
            userarray = readUser(ctx.message.author.id)
            userarray[CHEI] = str(Decimal(userarray[CHEI]) * Decimal(amount)) + newline
            if (float(userarray[CHEI]) > infinity):
                df.warn("Invalid size value.")
                await ctx.send("Too big. x_x", delete_after=3)
                userarray[CHEI] = str(infinity) + newline
            writeUser(ctx.message.author.id, userarray)
            userarray = readUser(ctx.message.author.id)
            if userarray[DISP] == "Y\n":
                await nickUpdate(ctx.message.author)
                await ctx.send("""<@{0}> is now {1} tall. ({2})""".format(ctx.message.author.id, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI]))) #Add comp to base.
        elif style == "s" or style == "-" or style == "sub" or style == "subtract":
            amount = isFeetAndInchesAndIfSoFixIt(amount)
            userarray = readUser(ctx.message.author.id)
            userarray[CHEI] = str(Decimal(userarray[CHEI]) - (toSV(getNum(amount), getLet(amount))))
            if (float(userarray[CHEI]) > infinity):
                df.warn("Invalid size value.")
                await ctx.send("Too big. x_x", delete_after=3)
                userarray[CHEI] = str(infinity) + newline
            writeUser(ctx.message.author.id, userarray)
            userarray = readUser(ctx.message.author.id)
            if userarray[DISP] == "Y\n":
                await nickUpdate(ctx.message.author)
                await ctx.send("""<@{0}> is now {1} tall. ({2})""".format(ctx.message.author.id, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI]))) #Add comp to base.
        elif style == "d" or style == "/" or style == "div" or style == "divide":
            userarray = readUser(ctx.message.author.id)
            userarray[CHEI] = str(Decimal(userarray[CHEI]) / Decimal(amount))
            if (float(userarray[CHEI]) > infinity):
                df.warn("Invalid size value.")
                await ctx.send("Too big. x_x", delete_after=3)
                userarray[CHEI] = str(infinity) + newline
            writeUser(ctx.message.author.id, userarray)
            userarray = readUser(ctx.message.author.id)
            if userarray[DISP] == "Y\n":
                await nickUpdate(ctx.message.author)
                await ctx.send("""<@{0}> is now {1} tall. ({2})""".format(ctx.message.author.id, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI]))) #Add comp to base.
        else:
            await ctx.send("Please enter a valid change method.", delete_after=3)
            return

    @commands.command()
    async def slowchange(self, ctx, style : str, amount : str, delay : float):
        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) slow-changed {style}-style {amount} every {delay} minutes.")
        async def slowchangetask(ctx, style, amount, delay):
            #Change height.
            if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
            #User file missing.
                await ctx.send("""Sorry! You aren't registered with SizeBot.
        To register, use the `&register` command.""", delete_after=5)
            elif style == "a" or style == "+" or style == "add":
                while True:
                    amount = isFeetAndInchesAndIfSoFixIt(amount)
                    userarray = readUser(ctx.message.author.id)
                    userarray[CHEI] = str(Decimal(userarray[CHEI]) + Decimal(toSV(getNum(amount), getLet(amount)))) + newline
                    if (float(userarray[CHEI]) > infinity):
                        df.warn("Invalid size value.")
                        await ctx.send("Too big. x_x", delete_after=3)
                        userarray[CHEI] = str(infinity) + newline
                        tasks[ctx.message.author.id].cancel()
                        del tasks[ctx.message.author.id]
                    writeUser(ctx.message.author.id, userarray)
                    userarray = readUser(ctx.message.author.id)
                    if userarray[DISP] == "Y\n":
                        await nickUpdate(ctx.message.author)
                    await ctx.send("""<@{0}> is now {1} tall. ({2})""".format(ctx.message.author.id, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])), delete_after = 5) #Add comp to base.
                    await asyncio.sleep(delay * 60)
            elif style == "m" or style == "*" or style == "x" or style == "mult" or style == "multiply":
                while True:
                    userarray = readUser(ctx.message.author.id)
                    userarray[CHEI] = str(Decimal(userarray[CHEI]) * Decimal(amount)) + newline
                    if (float(userarray[CHEI]) > infinity):
                        df.warn("Invalid size value.")
                        await ctx.send("Too big. x_x", delete_after=3)
                        uuserarray[CHEI] = str(infinity) + newline
                        tasks[ctx.message.author.id].cancel()
                        del tasks[ctx.message.author.id]
                    writeUser(ctx.message.author.id, userarray)
                    userarray = readUser(ctx.message.author.id)
                    if userarray[DISP] == "Y\n":
                        await nickUpdate(ctx.message.author)
                        await ctx.send("""{0} is now {1} tall. ({2})""".format(ctx.message.author.name, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])), delete_after = 5) #Add comp to base.
                        await asyncio.sleep(delay * 60)
            elif style == "s" or style == "-" or style == "sub" or style == "subtract":
                while True:
                    amount = isFeetAndInchesAndIfSoFixIt(amount)
                    userarray = readUser(ctx.message.author.id)
                    userarray[CHEI] = str(Decimal(userarray[CHEI]) - (toSV(getNum(amount), getLet(amount))))
                    writeUser(ctx.message.author.id, userarray)
                    userarray = readUser(ctx.message.author.id)
                    if userarray[DISP] == "Y\n":
                        await nickUpdate(ctx.message.author)
                        await ctx.send("""{0} is now {1} tall. ({2})""".format(ctx.message.author.name, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])), delete_after = 5) #Add comp to base.
                        await asyncio.sleep(delay * 60)
            elif style == "d" or style == "/" or style == "div" or style == "divide":
                while True:
                    userarray = readUser(ctx.message.author.id)
                    userarray[CHEI] = str(Decimal(userarray[CHEI]) / Decimal(amount))
                    writeUser(ctx.message.author.id, userarray)
                    userarray = readUser(ctx.message.author.id)
                    if userarray[DISP] == "Y\n":
                        await nickUpdate(ctx.message.author)
                        await ctx.send("""{0} is now {1} tall. ({2})""".format(ctx.message.author.name, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])), delete_after = 5) #Add comp to base.
                        await asyncio.sleep(delay * 60)
            else:
                await ctx.send("Please enter a valid change style.", delete_after=3)
        bot = self.bot
        try:
            tasks[ctx.message.author.id].cancel()
            del tasks[ctx.message.author.id]
        except:
            pass
        task = bot.loop.create_task(slowchangetask(ctx, style, amount, delay))
        tasks[ctx.message.author.id] = task

    @commands.command()
    async def stopchange(self, ctx):
        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) stopped slow-changing.")
        try:
            tasks[ctx.message.author.id].cancel()
            del tasks[ctx.message.author.id]
        except:
            await ctx.send("You can't stop slow-changing, as you don't have a task active!")
            df.warn(f"User {ctx.message.author.id} ({ctx.message.author.nick}) tried to stop slow-changing, but there didn't have a task active.")

    @commands.command()
    async def eatme(self, ctx):
        #Eat me!
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot.
    To register, use the `&register` command.""", delete_after=5)
        else:
            userarray = readUser(ctx.message.author.id)
            randmult = round(random.random(2, 20), 1)
            newheight = float(userarray[CHEI]) * randmult
            userarray[CHEI] = str(newheight) + newline
            if (float(userarray[CHEI]) > infinity):
                df.warn("Invalid size value.")
                await ctx.send("Too big. x_x", delete_after=3)
                userarray[CHEI] = str(infinity) + newline
            writeUser(ctx.message.author.id, userarray)
            userarray = readUser(ctx.message.author.id)
            if userarray[DISP] == "Y\n":
                await nickUpdate(ctx.message.author)
            df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) ate a cake and multiplied {randmult}.")
            #TODO: Randomize the italics message here.
            await ctx.send("""<@{0}> ate a :cake:! *I mean it said "Eat me..."*
They multiplied {1}x and are now {2} tall. ({3})""".format(ctx.message.author.id, randmult, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])))

    @commands.command()
    async def drinkme(self, ctx):
        #Drink me!
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot.
    To register, use the `&register` command.""", delete_after=5)
        else:
            userarray = readUser(ctx.message.author.id)
            randmult = round(random.random(2, 20), 1)
            newheight = float(userarray[CHEI]) / randmult
            userarray[CHEI] = str(newheight) + newline
            if (float(userarray[CHEI]) > infinity):
                df.warn("Invalid size value.")
                await ctx.send("Too big. x_x", delete_after=3)
                userarray[CHEI] = str(infinity) + newline
            writeUser(ctx.message.author.id, userarray)
            userarray = readUser(ctx.message.author.id)
            if userarray[DISP] == "Y\n":
                await nickUpdate(ctx.message.author)
            df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) drank a potion and divided {randmult}.")
            #TODO: Randomize the italics message here.
            await ctx.send("""<@{0}> drank a :shrinkpotion:! *What harm could a drink do?*
They shrunk {1}x and are now {2} tall. ({3})""".format(ctx.message.author.id, randmult, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])))



#Necessary.
def setup(bot):
    bot.add_cog(ChangeCog(bot))
