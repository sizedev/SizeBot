import random

from discord.ext import commands, tasks
from sizebot.discordplus import commandsplus

from sizebot import digilogger as logger
from sizebot import userdb
from sizebot.digiSV import Rate
from sizebot import digisize
from sizebot.checks import requireAdmin
from sizebot.lib import changes


class ChangeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        changes.loadFromFile()
        self.changeTask.start()

    def cog_unload(self):
        self.changeTask.cancel()

    @commandsplus.command(
        usage = "<x,-,/,+> <amount>"
    )
    @commands.guild_only()
    async def change(self, ctx, style, *, amount):
        """Change height"""
        userid = ctx.author.id

        digisize.changeUser(userid, style, amount)
        userdata = userdb.load(userid)

        await logger.info(f"User {userid} ({ctx.author.display_name}) changed {style}-style {amount}.")
        await ctx.send(f"User <@{userid}> is now {userdata.height:m} ({userdata.height:u}) tall.")

    @commandsplus.command(
        hidden = True
    )
    @commands.check(requireAdmin)
    async def changes(self, ctx):
        await ctx.message.delete(delay=0)

        changeDump = changes.formatSummary()

        if not changeDump:
            changeDump = "No changes"

        await ctx.author.send("**CHANGES**\n" + changeDump)
        await logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) dumped the running changes.")

    @commandsplus.command(
        usage = "<rate>"
    )
    @commands.guild_only()
    async def slowchange(self, ctx, *, rateStr: str):
        userid = ctx.author.id
        guildid = ctx.guild.id

        addPerSec, mulPerSec, stopSV, stopTV = Rate.parse(rateStr)

        changes.start(userid, guildid, addPerSec=addPerSec, mulPerSec=mulPerSec, stopSV=stopSV, stopTV=stopTV)

        await logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) slow-changed {addPerSec}/sec and *{mulPerSec}/sec until {stopSV} for {stopTV} seconds.")

    @commandsplus.command()
    @commands.guild_only()
    async def stopchange(self, ctx):
        userid = ctx.author.id
        guildid = ctx.guild.id

        deleted = changes.stop(userid, guildid)

        if deleted is None:
            await ctx.send("You can't stop slow-changing, as you don't have a task active!")
            await logger.warn(f"User {ctx.author.id} ({ctx.author.display_name}) tried to stop slow-changing, but there didn't have a task active.")
        else:
            await logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) stopped slow-changing.")

    @commandsplus.command()
    @commands.guild_only()
    async def eatme(self, ctx):
        """Eat me!"""
        userid = ctx.author.id

        randmult = round(random.random(2, 20), 1)
        digisize.changeUser(userid, "multiply", randmult)
        userdata = userdb.load(userid)

        # TODO: Randomize the italics message here
        await ctx.send(
            f"<@{userid}> ate a :cake:! *I mean it said \"Eat me...\"*\n"
            f"They multiplied {randmult}x and are now {userdata.height:m} tall. ({userdata.height:u})")
        await logger.info(f"User {userid} ({ctx.author.display_name}) ate a cake and multiplied {randmult}.")

    @commandsplus.command()
    @commands.guild_only()
    async def drinkme(self, ctx):
        """Drink me!"""
        userid = ctx.author.id

        userdata = userdb.load(userid)
        randmult = round(random.random(2, 20), 1)
        digisize.changeUser(ctx.author.id, "divide", randmult)

        # TODO: Randomize the italics message here
        await ctx.send(
            f"<@{ctx.author.id}> ate a :milk:! *I mean it said \"Drink me...\"*\n"
            f"They shrunk {randmult}x and are now {userdata.height:m} tall. ({userdata.height:u})")
        await logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) drank a potion and shrunk {randmult}.")

    @tasks.loop(seconds=6)
    async def changeTask(self):
        """Slow growth task"""
        changes.apply(self.bot)


def setup(bot):
    bot.add_cog(ChangeCog(bot))
