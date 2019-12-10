import random
import os

from discord.ext import commands

import digiformatter as df
import digierror as errors
from globalsb import changeUser, readUser, folder
from globalsb import fromSV, fromSVUSA
from globalsb import CHEI
from globalsb import tasks


class ChangeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def change(self, ctx, style, *, amount):
        # Change height.
        changereturn = changeUser(ctx.message.author.id, style, amount)
        errors.throw(ctx, changereturn)
        if changereturn == errors.SUCCESS:
            userfile = readUser(ctx.message.author.id)
            df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) changed {style}-style {amount}.")
            await ctx.send(f"User <@{ctx.message.author.id}> is now {fromSV(userfile[CHEI])} ({fromSVUSA(userfile[CHEI])}) tall.")

    # TODO: Switch to changeUser().
    @commands.command()
    async def slowchange(self, ctx, style: str, rate: str):
        # TODO: calculate these from rate?
        amount = ""
        delay = ""
        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) slow-changed {style}-style {amount} every {delay} minutes.")

        async def slowchangetask(ctx, style, amount, delay):
            # TODO: Implement this
            pass

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
        # Eat me!
        randmult = round(random.random(2, 20), 1)
        changereturn = changeUser(ctx.message.author.id, "multiply", randmult)
        errors.throw(ctx, changereturn)
        if changereturn == errors.SUCCESS:
            userfile = readUser(ctx.message.author.id)
            df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) ate a cake and multiplied {randmult}.")
            # TODO: Randomize the italics message here.
            await ctx.send(f"""<@{ctx.message.author.id}> ate a :cake:! *I mean it said "Eat me..."*
They multiplied {randmult}x and are now {fromSV(userfile[CHEI])} tall. ({fromSVUSA(userfile[CHEI])})""")

    @commands.command()
    async def drinkme(self, ctx):
        # Drink me!
        if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
            # User file missing.
            await ctx.send("""Sorry! You aren't registered with SizeBot.
To register, use the `&register` command.""", delete_after=5)
        else:
            randmult = round(random.random(2, 20), 1)
            changereturn = changeUser(ctx.message.author.id, "divide", randmult)
            errors.throw(ctx, changereturn)
            if changereturn == errors.SUCCESS:
                userfile = readUser(ctx.message.author.id)
                df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) drank a potion and shrunk {randmult}.")
                # TODO: Randomize the italics message here.
                await ctx.send(f"""<@{ctx.message.author.id}> ate a :milk:! *I mean it said "Drink me..."*
    They shrunk {randmult}x and are now {fromSV(userfile[CHEI])} tall. ({fromSVUSA(userfile[CHEI])})""")


# Necessary.
def setup(bot):
    bot.add_cog(ChangeCog(bot))
