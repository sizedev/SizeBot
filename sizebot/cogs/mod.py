import discord
from discord.ext import commands
from sizebot.discordplus import commandsplus

from sizebot import digilogger as logger
from sizebot.conf import conf
from sizebot import userdb
from sizebot.digiSV import SV, WV


class ModCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commandsplus.command()
    async def heightunits(self, ctx):
        units = "\n".join(str(u) for u in sorted(SV._units))
        embed = discord.Embed(title="Units")
        embed.add_field(title="Height", value=units)
        await ctx.send(embed=embed)

    @commandsplus.command()
    async def weightunits(self, ctx):
        await ctx.send("```" + ("\n".join(str(u) for u in sorted(WV._units))) + "```")

    @commandsplus.command()
    async def help(self, ctx, what: str = None):
        await ctx.message.delete(delay=0)
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

    @commandsplus.command()
    async def about(self, ctx):
        await ctx.message.delete(delay=0)
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

    @commandsplus.command()
    async def donate(self, ctx):
        await ctx.message.delete(delay=0)
        await ctx.send(
            f"<@{ctx.message.author.id}>\n"
            "SizeBot is coded (mainly) by DigiDuncan, and for absolutely free.\n"
            "However, if you wish to contribute to DigiDuncan directly, you can do so here:\n"
            "https://ko-fi.com/DigiDuncan\n"
            "SizeBot has been a passion project coded over a period of two years and learning a lot of Python along the way.\n"
            "Thank you so much for being here throughout this journey!")

    @commandsplus.command()
    async def bug(self, ctx, *, message: str):
        await logger.warn(f"{ctx.message.author.id} ({ctx.message.author.name}) sent a bug report.")
        await self.bot.get_user(conf.getId("DigiDuncan")).send(f"<@{ctx.message.author.id}>: {message}")


def setup(bot):
    bot.add_cog(ModCog(bot))
