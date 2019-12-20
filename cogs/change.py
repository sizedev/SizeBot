import random
from decimal import Decimal

from discord.ext import commands, tasks

import digiformatter as df
import digierror as errors
import userdb
from userdb import CHEI
import digiSV
import digisize


class Change:
    def __init__(self, userid, *, addPerSec=0, mulPerSec=1):
        self.userid = userid
        self.addPerSec = Decimal(addPerSec)
        self.mulPerSec = Decimal(mulPerSec)

    def apply(self, seconds):
        user = userdb.load(self.userid)
        seconds = Decimal(seconds)
        addPerTick = seconds * self.addPerSec
        mulPerTick = self.mulPerTick ** seconds
        user.height = (user.height * mulPerTick) + addPerTick
        userdb.save()
        digisize.nickUpdate(self.userid)


class ChangeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.changes = {}

    @commands.command()
    async def change(self, ctx, style, *, amount):
        # Change height.
        changereturn = digisize.changeUser(ctx.message.author.id, style, amount)
        errors.throw(ctx(changereturn))
        if changereturn == errors.SUCCESS:
            userdata = userdb.load(ctx.message.author.id)
            df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) changed {style}-style {amount}.")
            await ctx.send(f"User <@{ctx.message.author.id}> is now {digiSV.fromSV(userdata.height, 'm')} ({digiSV.fromSV(userdata.height, 'u')}) tall.")

    # TODO: Switch to digisize.changeUser().
    @commands.command()
    async def slowchange(self, ctx, style: str, rate: str):
        # TODO: calculate these from rate?
        amount = ""
        delay = ""
        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) slow-changed {style}-style {amount} every {delay} minutes.")

        change = Change(ctx.message.author.id, addPerSec=0, mulPerSec=1)

        self.changes[ctx.message.author.id] = change

    @commands.command()
    async def stopchange(self, ctx):
        df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) stopped slow-changing.")

        deleted = self.changes.pop(ctx.message.author.id, None)

        if deleted is None:
            await ctx.send("You can't stop slow-changing, as you don't have a task active!")
            df.warn(f"User {ctx.message.author.id} ({ctx.message.author.nick}) tried to stop slow-changing, but there didn't have a task active.")

    @commands.command()
    async def eatme(self, ctx):
        # Eat me!
        randmult = round(random.random(2, 20), 1)
        changereturn = digisize.changeUser(ctx.message.author.id, "multiply", randmult)
        errors.throw(ctx(changereturn))
        if changereturn == errors.SUCCESS:
            userdata = userdb.load(ctx.message.author.id)
            df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) ate a cake and multiplied {randmult}.")
            # TODO: Randomize the italics message here.
            await ctx.send(f"""<@{ctx.message.author.id}> ate a :cake:! *I mean it said "Eat me..."*
They multiplied {randmult}x and are now {digiSV.fromSV(userdata[CHEI], 'm')} tall. ({digiSV.fromSV(userdata[CHEI], 'u')})""")

    @commands.command()
    async def drinkme(self, ctx):
        # Drink me!
        userdata = userdb.load(ctx.message.author.id)
        randmult = round(random.random(2, 20), 1)
        changereturn = digisize.changeUser(ctx.message.author.id, "divide", randmult)
        errors.throw(ctx(changereturn))
        if changereturn == errors.SUCCESS:
            df.msg(f"User {ctx.message.author.id} ({ctx.message.author.nick}) drank a potion and shrunk {randmult}.")
            # TODO: Randomize the italics message here.
            await ctx.send(f"""<@{ctx.message.author.id}> ate a :milk:! *I mean it said "Drink me..."*
    They shrunk {randmult}x and are now {digiSV.fromSV(userdata[CHEI], 'm')} tall. ({digiSV.fromSV(userdata[CHEI], 'u')})""")

    # Slow growth task
    # TODO: Does this restart if there are errors?
    @tasks.loop(seconds=6)
    async def changeTask(self):
        for change in self.changes.values():
            change.apply()


# Necessary.
def setup(bot):
    bot.add_cog(ChangeCog(bot))
