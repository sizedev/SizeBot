import discord
from discord.ext import commands
from globalsb import *

class ModCog:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def repeat(self, ctx, delay : float, *, message : str):
        await ctx.message.delete()
        async def repeattask():
            while True:
                await ctx.send(message)
                await asyncio.sleep(delay * 60)
        task = bot.loop.create_task(repeattask())
        tasks[ctx.message.author.id] = task

    @commands.command()
    async def stoprepeat(self, ctx):
        await ctx.message.delete()
        tasks[ctx.message.author.id].cancel()
        del tasks[ctx.message.author.id]

    @commands.command()
    async def say(self, ctx, *, message : str):
        await ctx.message.delete()
        if ctx.message.author.id == digiid:
            await ctx.send(message)

    @commands.command()
    async def sing(self, ctx, *, string : str):
        await ctx.message.delete()
        newstring = ":musical_score: *" + string + "* :musical_note:"
        await ctx.send(newstring)

    @commands.command()
    async def heightunits(self, ctx):
        await ctx.message.delete()
        await ctx.send("""<@{0}>, **Accepted Units**
    *Height*
    ```+--------------------+--------------------------------+
    |       Metric            |         Imperial          |
    +--------------------+--------------------------------+
    | ym (yoctometer[s])      | in (inch[es])             |
    | zm (zeptometer[s])      | ft (feet)                 |
    | am (attometer[s])       | mi (mile[s])              |
    | fm (femtometer[s])      | AU (astronomical_unit[s]) |
    | pm (picometer[s])       | uni (universe[s])         |
    | nm (nanometer[s])       |                           |
    | µm (micrometer[s])      |                           |
    | mm (millimeter[s])      |                           |
    | cm (centimeter[s])      |                           |
    | m (meter[s])            |                           |
    | km (kilometer[s])       |                           |
    | Mm (megameter[s])       |                           |
    | Gm (gigameter[s])       |                           |
    | Tm (terameter[s])       |                           |
    | Pm (petameter[s])       |                           |
    | Em (exameter[s])        |                           |
    | Zm (zettameter[s])      |                           |
    | Ym (yottameter[s])      |                           |
    | uni (universe[s])       |                           |
    | kuni (kilouniverse[s])  |                           |
    | Muni (megauniverse[s])  |                           |
    | Guni (gigauniverse[s])  |                           |
    | Tuni (terauniverse[s])  |                           |
    | Puni (petauniverse[s])  |                           |
    | Euni (exauniverse[s])   |                           |
    | Zuni (zettauniverse[s]) |                           |
    | Yuni (yottauniverse[s]) |                           |
    +--------------------+--------------------------------+```""".format(ctx.message.author.id))

    @commands.command()
    async def weightunits(self, ctx):
        await ctx.message.delete()
        await ctx.send("""<@{0}>, **Accepted Units**
    *Weight*
    ```+--------------------+--------------------------------+
    |       Metric            |         Imperial          |
    +--------------------+--------------------------------+
    | yg (yoctogram[s])       | oz (ounce[s])             |
    | zg (zeptogram[s])       | lbs (pound[s])            |
    | ag (attogram[s])        | Earth[s]                  |
    | fg (femtogram[s])       | Sun[s]                    |
    | pg (picogram[s])        |                           |
    | ng (nanogram[s])        |                           |
    | µg (microgram[s])       |                           |
    | mg (milligram[s])       |                           |
    | g (gram[s])             |                           |
    | kg (kilogram[s])        |                           |
    | t (ton[s])              |                           |
    | kt (kiloton[s])         |                           |
    | Mt (megaton[s])         |                           |
    | Gt (gigaton[s])         |                           |
    | Tt (teraton[s])         |                           |
    | Pt (petaton[s])         |                           |
    | Et (exaton[s])          |                           |
    | Zt (zettaton[s])        |                           |
    | Yt (yottaton[s])        |                           |
    | uni (universe[s])       |                           |
    | kuni (kilouniverse[s])  |                           |
    | Muni (megauniverse[s])  |                           |
    | Guni (gigauniverse[s])  |                           |
    | Tuni (terauniverse[s])  |                           |
    | Puni (petauniverse[s])  |                           |
    | Euni (exauniverse[s])   |                           |
    | Zuni (zettauniverse[s]) |                           |
    | Yuni (yottauniverse[s]) |                           |
    +--------------------+--------------------------------+```""".format(ctx.message.author.id))

    @commands.command()
    async def help(self, ctx, what:str = None):
        await ctx.message.delete()
        if what is None:
            await ctx.send("""<@{0}>, **Help Topics**
    note, [] indicates a required parameter, <> indicates an option parameter.
    *Commands*
    ```register [nickname] [Y/N] [current height] [base height] [base weight] [U/M] <species>
    unregister
    stats <user>
    change [x,/,+,-] [value]
    setheight [height]
    set0
    setinf
    setbaseheight [height]
    setbaseweight [weight]
    setrandomheight [minheight] [maxheight]
    slowchange [x,/,+,-] [amount] [delay]
    stopchange
    roll XdY
    changenick [nick]
    setspecies [species]
    clearspecies
    setdisplay [Y/N]
    compare [user1] <user2>
    sing [string]```

    *Other Topics*
    ```heightunits
    weightunits
    about
    bug```""".format(ctx.message.author.id))

    @commands.command()
    async def about(self, ctx):
        await ctx.message.delete()
        await ctx.send("```" + ascii + "```")
        await ctx.send("""<@{0}>
    ***SizeBot3 by DigiDuncan***
    *A big program for big people.*
    **Written for the Macropolis server**
    **Slogan** **by Twitchy**
    **Additional equations** *by Benyovski*
    **Alpha Tested** *by AWK_*
    **Beta Tested** *by Speedbird 001, worstgender, Arceus3251*
    **written in** *Python 3.6 with discord.py*
    **written with** Sublime Text
    **Special thanks** *to Noboru for making the Macropolis server*
    **Special thanks** *to the discord.py Community Discord for helping with code*
    **Special thanks** to the {1} users of SizeBot3.
    *Tana helped out a little bit. <3*

    "She (*SizeBot*) is beautiful." -- *GoddessArete*
    ":100::thumbsup:" -- *Anonymous*
    "I am the only person who has accidentally turned my fetish into a tech support job." -- *DigiDuncan*

    Version {2} | 04 Apr 2018""".format(ctx.message.author.id, members, version))

    @commands.command()
    async def bug(self, ctx, *, message : str):
        await bot.get_user(digiid).send("<@{0}>: {1}".format(ctx.message.author.id, message))

#Necessary.
def setup(bot):
    bot.add_cog(ModCog(bot))