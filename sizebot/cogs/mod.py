import math
from datetime import datetime

import discord
from discord.ext import commands
from sizebot.discordplus import commandsplus

from sizebot import digilogger as logger
from sizebot.conf import conf
from sizebot import userdb
from sizebot.digiSV import SV, WV
from sizebot.utils import chunkList


class ModCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commandsplus.command()
    async def units(self, ctx):
        heightunits = [str(u) for u in sorted(SV._units)]
        weightunits = [str(u) for u in sorted(WV._units)]

        embed = discord.Embed(title="Units")

        for n, units in enumerate(chunkList(heightunits, math.ceil(len(heightunits) / 3))):

            embed.add_field(name="Height" if n == 0 else "\u200b", value="\n".join(units))

        for n, units in enumerate(chunkList(weightunits, math.ceil(len(weightunits) / 3))):
            embed.add_field(name="Weight" if n == 0 else "\u200b", value="\n".join(units))

        await ctx.send(embed=embed)

    async def send_bot_help(self, ctx, bot):
        embed = discord.Embed(title="Help")

        commands = sorted((c for c in bot.commands if not c.hidden), key=lambda c: c.name)
        commandLines = "\n".join(f"{c.name} - {c.short_doc}" for c in commands)
        embed.add_field(name="Commands", value=commandLines)
        await ctx.send(embed=embed)

    async def send_command_help(self, ctx, cmd):
        if len(cmd.aliases) > 0:
            name = f"[{cmd.name}|{'|'.join(cmd.aliases)}]"
        else:
            name = cmd.name
        signature = f"{ctx.prefix}{name} {cmd.signature}"

        if cmd.description:
            desc = cmd.description + "\n\n" + cmd.help
        else:
            desc = cmd.help

        embed = discord.Embed(
            title=f"{signature}",
            description=desc
        ).set_author(name=f"Help")

        await ctx.send(embed=embed)

    @commandsplus.command()
    async def help(self, ctx, cmdName: str = None):
        bot = ctx.bot
        if cmdName is None:
            await self.send_bot_help(ctx, bot)
            return

        cmd = bot.all_commands.get(cmdName)
        if cmd:
            await self.send_command_help(ctx, cmd)
            return

        await ctx.send(f"Unrecognized command: {cmdName}")

    @commandsplus.command()
    async def about(self, ctx):
        now = datetime.now()
        await ctx.message.delete(delay=0)
        await ctx.send(
            "```\n"
            f"{conf.banner}\n"
            "```\n")
        await ctx.send(
            f"<@{ctx.message.author.id}>\n"
            "***SizeBot3½ by DigiDuncan***\n"
            "*A big program for big people.*\n"  # TODO: Change this slogan.
            "**Written for** *Size Matters*\n"
            "**Coding Assistance** *by Natalie*\n"
            "**Additional equations** *by Benyovski and Arceus3251*\n"
            "**Alpha Tested** *by AWK_*\n"
            "**Beta Tested** *by Speedbird 001, worstgender, Arceus3251, and Kelly*\n"
            "**written in** *Python 3.7 with discord.py rewrite*\n"
            "**written with** *Atom* and *Visual Studio Code*\n"
            "**Special thanks** *to Reol, jyubari, and Memekip for making the Size Matters server, and Yukio and SpiderGnome for helping moderate it.*\n"
            "**Special thanks** *to the discord.py Community Discord for helping with code*\n"
            f"**Special thanks** *to the {userdb.count()} users of SizeBot3½.*\n"
            "\n"
            "\"She [*SizeBot*] is beautiful.\" -- *GoddessArete*\n"
            "\":100::thumbsup:\" -- *Anonymous*\n"
            "\"I want to put SizeBot in charge of the world government.\" -- *AWK*\n"
            "\"Um... I like it?\" -- *Goddess Syn*\n"
            "\"I am the only person who has accidentally turned my fetish into a tech support job.\" -- *DigiDuncan*\n"
            "\n"
            f"Version {conf.version} | {now.strftime('%d %b %Y')}")

    @commandsplus.command()
    async def donate(self, ctx):
        await ctx.message.delete(delay=0)
        await ctx.send(
            f"<@{ctx.message.author.id}>\n"
            "SizeBot is coded (mainly) and hosted by DigiDuncan, and for absolutely free.\n"
            "However, if you wish to contribute to DigiDuncan directly, you can do so here:\n"
            "https://ko-fi.com/DigiDuncan\n"
            "SizeBot has been a passion project coded over a period of three years and learning a lot of Python along the way.\n"
            "Thank you so much for being here throughout this journey!")

    @commandsplus.command()
    async def bug(self, ctx, *, message: str):
        await logger.warn(f"{ctx.message.author.id} ({ctx.message.author.name}) sent a bug report.")
        await self.bot.get_user(conf.getId("DigiDuncan")).send(f"<@{ctx.message.author.id}>: {message}")

    @commandsplus.command()
    async def ping(self, ctx):
        await ctx.send('Pong! :ping_pong: {0}s'.format(round(self.bot.latency, 3)))


def setup(bot):
    bot.add_cog(ModCog(bot))
