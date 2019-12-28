from discord.ext import commands

from sizebot import digilogger as logger
from sizebot.conf import conf
from sizebot import userdb


class ModCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def heightunits(self, ctx):
        await ctx.message.delete()
        await ctx.send(
            f"<@{ctx.message.author.id}>, **Accepted Units**\n"
            "*Height*\n"
            "```\n"
            "┌─────────────────────────┬───────────────────────────┐\n"
            "│       Metric            │         Imperial          │\n"
            "├─────────────────────────┼───────────────────────────┤\n"
            "│ ym (yoctometer[s])      │ in (inch[es])             │\n"
            "│ zm (zeptometer[s])      │ ft (feet)                 │\n"
            "│ am (attometer[s])       │ mi (mile[s])              │\n"
            "│ fm (femtometer[s])      │ AU (astronomical_unit[s]) │\n"
            "│ pm (picometer[s])       │ uni (universe[s])         │\n"
            "│ nm (nanometer[s])       │                           │\n"
            "│ µm (micrometer[s])      │                           │\n"
            "│ mm (millimeter[s])      │                           │\n"
            "│ cm (centimeter[s])      │                           │\n"
            "│ m (meter[s])            │                           │\n"
            "│ km (kilometer[s])       │                           │\n"
            "│ Mm (megameter[s])       │                           │\n"
            "│ Gm (gigameter[s])       │                           │\n"
            "│ Tm (terameter[s])       │                           │\n"
            "│ Pm (petameter[s])       │                           │\n"
            "│ Em (exameter[s])        │                           │\n"
            "│ Zm (zettameter[s])      │                           │\n"
            "│ Ym (yottameter[s])      │                           │\n"
            "│ uni (universe[s])       │                           │\n"
            "│ kuni (kilouniverse[s])  │                           │\n"
            "│ Muni (megauniverse[s])  │                           │\n"
            "│ Guni (gigauniverse[s])  │                           │\n"
            "│ Tuni (terauniverse[s])  │                           │\n"
            "│ Puni (petauniverse[s])  │                           │\n"
            "│ Euni (exauniverse[s])   │                           │\n"
            "│ Zuni (zettauniverse[s]) │                           │\n"
            "│ Yuni (yottauniverse[s]) │                           │\n"
            "└─────────────────────────┴───────────────────────────┘\n"
            "```")

    @commands.command()
    async def weightunits(self, ctx):
        await ctx.message.delete()
        await ctx.send(
            f"<@{ctx.message.author.id}>, **Accepted Units**\n"
            "*Weight*\n"
            "```\n"
            "┌─────────────────────────┬───────────────────────────┐\n"
            "│       Metric            │         Imperial          │\n"
            "├─────────────────────────┼───────────────────────────┤\n"
            "│ yg (yoctogram[s])       │ oz (ounce[s])             │\n"
            "│ zg (zeptogram[s])       │ lbs (pound[s])            │\n"
            "│ ag (attogram[s])        │ Earth[s]                  │\n"
            "│ fg (femtogram[s])       │ Sun[s]                    │\n"
            "│ pg (picogram[s])        │                           │\n"
            "│ ng (nanogram[s])        │                           │\n"
            "│ µg (microgram[s])       │                           │\n"
            "│ mg (milligram[s])       │                           │\n"
            "│ g (gram[s])             │                           │\n"
            "│ kg (kilogram[s])        │                           │\n"
            "│ t (ton[s])              │                           │\n"
            "│ kt (kiloton[s])         │                           │\n"
            "│ Mt (megaton[s])         │                           │\n"
            "│ Gt (gigaton[s])         │                           │\n"
            "│ Tt (teraton[s])         │                           │\n"
            "│ Pt (petaton[s])         │                           │\n"
            "│ Et (exaton[s])          │                           │\n"
            "│ Zt (zettaton[s])        │                           │\n"
            "│ Yt (yottaton[s])        │                           │\n"
            "│ uni (universe[s])       │                           │\n"
            "│ kuni (kilouniverse[s])  │                           │\n"
            "│ Muni (megauniverse[s])  │                           │\n"
            "│ Guni (gigauniverse[s])  │                           │\n"
            "│ Tuni (terauniverse[s])  │                           │\n"
            "│ Puni (petauniverse[s])  │                           │\n"
            "│ Euni (exauniverse[s])   │                           │\n"
            "│ Zuni (zettauniverse[s]) │                           │\n"
            "│ Yuni (yottauniverse[s]) │                           │\n"
            "└─────────────────────────┴───────────────────────────┘\n"
            "```")

    @commands.command()
    async def help(self, ctx, what: str = None):
        await ctx.message.delete()
        if what is None:
            await ctx.send(
                f"<@{ctx.message.author.id}>, **Help Topics**\n"
                "***☞*** *`[]` indicates a required parameter, `<>` indicates an optional parameter.*\n"
                "\n"
                "*Commands*\n"
                "```\n"
                "register \"[nickname]\" [Y/N]† [current height] [base height] [base weight] [U/M]†† \"<species>\"```\n"
                "*† Indicates whether you want SizeBot to automatically set and continue to manage your nickname and sizetag.*\n"
                "*†† Indicates which system to use for your sizetag. U = US, M = metric.*\n"
                "```\n"
                "unregister\n"
                "stats <user/size>\n"
                "change [x,/,+,-] [value]\n"
                "setheight [height]\n"
                "set0\n"
                "setinf\n"
                "setbaseheight [height]\n"
                "setbaseweight [weight]\n"
                "setrandomheight [minheight] [maxheight]\n"
                "slowchange [x,/,+,-] [amount] [delay]\n"
                "stopchange\n"
                "roll XdY\n"
                "changenick [nick]\n"
                "setspecies [species]\n"
                "clearspecies\n"
                "setdisplay [Y/N]\n"
                "setsystem [M/U]\n"
                "compare [user/size 1] <user/size 2>\n"
                "sing [string]```\n"
                "\n"
                "*Other Topics*\n"
                "```\n"
                "heightunits\n"
                "weightunits\n"
                "about\n"
                "donate\n"
                "bug\n"
                "```\n")

    @commands.command()
    async def about(self, ctx):
        await ctx.message.delete()
        await ctx.send(
            "```\n"
            f"{conf.banner}\n"
            "```\n")
        await ctx.send(
            f"<@{ctx.message.author.id}>\n"
            "***SizeBot3 by DigiDuncan***\n"
            "*A big program for big people.*\n"
            "**Written for** *the Size Haven server* and **adapted for** *Size Matters*\n"
            "**Slogan** *by Twitchy*\n"
            "**Additional equations** *by Benyovski and Arceus3251*\n"
            "**Coding Assistance** *by Natalie*\n"
            "**Alpha Tested** *by AWK_*\n"
            "**Beta Tested** *by Speedbird 001, worstgender, Arceus3251*\n"
            "**written in** *Python 3.7 with discord.py rewrite*\n"
            "**written with** *Atom*\n"
            "**Special thanks** *to Reol, jyubari, and Memekip for making the Size Matters server*\n"
            "**Special thanks** *to the discord.py Community Discord for helping with code*\n"
            f"**Special thanks** *to the {userdb.count()} users of SizeBot3.*\n"
            "\n"
            "\"She (*SizeBot*) is beautiful.\" -- *GoddessArete*\n"
            "\":100::thumbsup:\" -- *Anonymous*\n"
            "\"I want to put SizeBot in charge of the world government.\" -- *AWK*\n"
            "\"Um... I like it?\" -- *Goddess Syn*\n"
            "\"I am the only person who has accidentally turned my fetish into a tech support job.\" -- *DigiDuncan*\n"
            "\n"
            f"Version {conf.version} | 19 Jul 2019")

    @commands.command()
    async def donate(self, ctx):
        await ctx.message.delete()
        await ctx.send(
            f"<@{ctx.message.author.id}>\n"
            "SizeBot is coded (mainly) by DigiDuncan, and for absolutely free.\n"
            "However, if you wish to contribute to DigiDuncan directly, you can do so here:\n"
            "https://ko-fi.com/DigiDuncan\n"
            "SizeBot has been a passion project coded over a period of two years and learning a lot of Python along the way.\n"
            "Thank you so much for being here throughout this journey!")

    @commands.command()
    async def bug(self, ctx, *, message: str):
        await logger.warn(f"{ctx.message.author.id} ({ctx.message.author.name}) sent a bug report.")
        await self.bot.get_user(conf.getId("DigiDuncan")).send(f"<@{ctx.message.author.id}>: {message}")


# Necessary.
def setup(bot):
    bot.add_cog(ModCog(bot))
