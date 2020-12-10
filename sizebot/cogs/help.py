import logging
import math

from datetime import datetime

from discord import Embed
from discord.errors import Forbidden
from discord.ext import commands

from sizebot import __version__
from sizebot.conf import conf
from sizebot.lib import checks, objs, userdb, utils
from sizebot.lib.constants import colors, emojis, ids
from sizebot.lib.menu import Menu
from sizebot.lib.units import SV, WV

logger = logging.getLogger("sizebot")

# name
# description
#     The message prefixed into the default help command.
# help = inspect.cleandoc(self.__doc__)
#     The long help text for the command.
# brief
#     The short help text for the command.
# short_doc = self.brief or help.split("\n")[0]
#     Gets the “short” documentation of a command.
# usage = ""
#     A replacement for arguments in the default help text.
# signature
#     Returns a POSIX-like signature useful for help command output.
# hidden = False
#     If True, the default help command does not show this in the help output.
# aliases = []


def get_cat_cmds(commands):
    # Get all non-hidden commands, sorted by name
    commands = (c for c in commands if not c.hidden)
    commands = sorted(commands, key=lambda c: c.name)

    # Divide commands into categories
    commands_by_cat = {cat.cid: [] for cat in categories}

    for c in commands:
        cmd_category = c.category or "misc"
        if cmd_category not in commands_by_cat:
            logger.warn(f"Command category {cmd_category!r} does not exist.")
            cmd_category = "misc"
        commands_by_cat[cmd_category].append(c)
    return commands_by_cat


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        category = "help"
    )
    async def units(self, ctx):
        """Get a list of the various units SizeBot accepts."""
        heightobjectunits = [su.unit for su in SV._systems["o"]._systemunits]
        weightobjectunits = [su.unit for su in WV._systems["o"]._systemunits]

        heightunits = [str(u) for u in sorted(SV._units) if u not in heightobjectunits]
        weightunits = [str(u) for u in sorted(WV._units) if u not in weightobjectunits]

        embed = Embed(title=f"Units [SizeBot {__version__}]")

        for n, units in enumerate(utils.chunkList(heightunits, math.ceil(len(heightunits) / 3))):
            embed.add_field(name="Height" if n == 0 else "\u200b", value="\n".join(units))

        for n, units in enumerate(utils.chunkList(weightunits, math.ceil(len(weightunits) / 3))):
            embed.add_field(name="Weight" if n == 0 else "\u200b", value="\n".join(units))

        await ctx.send(embed=embed)

    @commands.command(
        aliases = ["objects"],
        category = "help"
    )
    async def objs(self, ctx):
        """Get a list of the various objects SizeBot accepts."""
        objectunits = []
        for obj in objs.objects:
            objectunits.append(obj.name)

        objectunits.sort()

        embed = Embed(title=f"Objects [SizeBot {__version__}]", description = f"*NOTE: All of these objects have multiple aliases. If there is an alias that you think should work for a listed object but doesn't, report it with `{ctx.prefix}suggestobject` and note that it's an alias.*")

        for n, units in enumerate(utils.chunkList(objectunits, math.ceil(len(objectunits) / 6))):
            embed.add_field(name="Objects" if n == 0 else "\u200b", value="\n".join(units))

        await ctx.send(embed=embed)

    async def send_summary_help(self, ctx):
        """Sends help summary.

        Help

        Commands

        {cmd.name} - {cmd.brief (or first line of cmd.help)}
        {cmd.name} - {cmd.brief (or first line of cmd.help)}
        ...
        """

        # Get commands grouped by category
        commands_by_cat = get_cat_cmds(ctx.bot.commands)

        embed = Embed(title=f"Help [SizeBot {__version__}]")
        embed.set_footer(text = "Select an emoji to see details about a category.")
        embed.set_author(name = ctx.author.name, icon_url = ctx.author.avatar_url)

        # Add each category to a field
        for cat in categories:
            cat_cmds = commands_by_cat.get(cat.cid, [])
            if not cat_cmds:
                logger.warn(f"Command category {cat.cid!r} is empty.")
                continue
            field_text = f"\n\n**{cat.emoji} {cat.name}**\n" + (", ".join(f"`{c.name}`" for c in cat_cmds))
            embed.add_field(value=field_text, inline=False)

        # Display the embed with a reaction menu
        categoryoptions = {cat.emoji: cat for cat in categories if commands_by_cat.get(cat.cid, [])}

        reactionmenu, answer = await Menu.display(
            ctx,
            categoryoptions.keys(),
            cancel_emoji = emojis.cancel,
            initial_embed = embed,
            delete_after = False
        )

        # User clicked cancel emoji or menu timed out
        if not answer:
            return

        # User clicked a category emoji
        await reactionmenu.message.delete()
        selectedcategory = categoryoptions[answer]
        cat_cmds = commands_by_cat.get(selectedcategory.cid, [])
        await self.send_category_help(ctx, selectedcategory, cat_cmds)

    async def send_category_help(self, ctx, category, cmds):
        # Prepare the embed for the category
        embed = Embed(title=f"{category.name} Help [SizeBot {__version__}]")
        embed.set_author(name = ctx.author.name, icon_url = ctx.author.avatar_url)

        command_texts = [f"`{c.name}` {c.alias_string}\n{c.short_doc}" for c in cmds]
        embed.add_field(value=f"**{category.emoji}{category.name}**", inline=False)
        field_texts = [""]
        for t in command_texts:
            if len(field_texts[-1] + "\n" + t) > 1024:
                field_texts.append("")
            field_texts[-1] = field_texts[-1] + "\n" + t
        for text in field_texts:
            embed.add_field(value=text)

        # Display the embed with a reaction menu
        reactionmenu, answer = await Menu.display(
            ctx,
            ["🔙"],
            cancel_emoji = emojis.cancel,
            initial_embed = embed,
            delete_after = False
        )

        # User clicked cancel emoji or menu timed out
        if not answer:
            return

        # User clicked the back emoji
        await reactionmenu.message.delete()
        await self.send_summary_help(ctx)

    async def send_command_help(self, ctx, cmd):
        """Sends help for a command.

        Help

        {prefix}{cmd.name} {cmd.usage (or autogenerated signature)}

        {cmd.description (optional)}

        {cmd.help (docstring, optional)}

        Aliases:
        alias1, alias2
        """
        signature = f"{ctx.prefix}{cmd.name} {cmd.signature}"

        descriptionParts = []
        if cmd.description:
            descriptionParts.append(cmd.description)
        if cmd.help:
            descriptionParts.append(cmd.help)
        description = ""
        if "is_owner" in repr(cmd.checks):
            description += ":rotating_light: **THIS COMMAND IS FOR BOT OWNERS ONLY** :rotating_light:\n"
        if "is_mod" in repr(cmd.checks):
            description += ":rotating_light: **THIS COMMAND IS FOR SERVER MODS ONLY** :rotating_light:\n"
        if "guild_only" in repr(cmd.checks):
            description += "*This command can only be run in a server, and not in DMs.*\n"
        description += "\n\n".join(descriptionParts).replace("&", ctx.prefix)

        embed = Embed(
            title=signature,
            description=description
        ).set_author(name=f"Help [SizeBot {__version__}]").set_footer(text=f"See `{conf.prefix}help <command> for more details about a command and how to use it.")

        if cmd.aliases:
            embed.add_field(name="**Aliases:**", value=", ".join(cmd.aliases), inline=False)

        await ctx.send(embed=embed)

    @commands.command(
        description="[description]",
        usage="[usage]",
        aliases=["helpme", "wtf"],
        category = "help"
    )
    async def help(self, ctx, cmdName: str = None):
        """[cmd.help[0]]

        [cmd.help[2]]
        [cmd.help[3]]
        """
        bot = ctx.bot
        if cmdName is None:
            await self.send_summary_help(ctx)
            return

        cmd = bot.all_commands.get(cmdName)
        if cmd:
            await self.send_command_help(ctx, cmd)
            return

        await ctx.send(f"Unrecognized command: `{cmdName}`.")

    @commands.command(
        category = "help"
    )
    async def about(self, ctx):
        """Get the credits and some facts about SizeBot."""
        now = datetime.now()
        embed = Embed(title = "SizeBot3½", description = "Think of a new slogan!", color = colors.cyan)
        embed.set_author(name = "DigiDuncan")
        embed.set_image(url = "https://cdn.discordapp.com/attachments/650460192009617433/698529527965417552/sizebotlogot.png")
        embed.add_field(name = "Credits",
                        value = ("**Coding Assistance** *by Natalie*\n"
                                 "**Additional Equations** *by Benyovski and Arceus3251*\n"
                                 "**Originally Tested** *by AWK, Kelly, worstgender, and Arceus3251*\n"),
                        inline = False)
        embed.add_field(name = "Servers",
                        value = ("**[Size Matters](https://discord.gg/UbMxrW)**: a size server moderated by DigiDuncan and others *(see below)*"),
                        inline = False)
        embed.add_field(name = "Technical Details",
                        value = "Written in Python 3.6, and slowly upgraded to 3.9. Originally written using Atom, and now Visual Studio Code. External libraries used are `discord.py` (rewrite version), `digiformatter` (my personal terminal-formatting library), and various dependencies you can find on the GitHub page.",
                        inline = False)
        embed.add_field(name = "Special Thanks",
                        value = ("**Special thanks** *to Reol, jyubari, and Memekip for making the Size Matters server, and Yukio and SpiderGnome for helping moderate it.*\n"
                                 "**Special thanks** *to Chocola, the creator of [Mei](https://chocola.codes/) and Arachne, for inspiration and moral support.*\n"
                                 "**Special thanks** *to the discord.py Community Discord for helping with code.*\n"
                                 f"**Special thanks** *to the {userdb.countusers()} users of SizeBot3½.*"),
                        inline = False)
        embed.add_field(name = "Testimonials",
                        value = ("\"I want to put SizeBot in charge of the world government.\" *-- AWK*\n"
                                 "\"Insanity is doing the exact same thing over and over again expecting things to change.\" *-- Chocola*\n"
                                 "\"Um... I like it?\" *-- Goddess Syn*\n"
                                 "\"I fixed the bot.\" *-- Natalie*\n"
                                 "\"I am the only person who has accidentally turned my fetish into a tech support job.\" *-- DigiDuncan*\n"
                                 "\"Insanity is doing the exact same thing over and over again expecting things to change.\" *-- Chocola*\n"),
                        inline = False)
        embed.set_footer(text = f"Version {__version__} | {now.strftime('%d %b %Y')}")
        await ctx.send(embed = embed)

    @commands.command(
        aliases = ["fund"],
        category = "help"
    )
    async def donate(self, ctx):
        """Give some monetary love to your favorite bot developer!"""
        await ctx.send(
            f"<@{ctx.author.id}>\n"
            "SizeBot is coded (mainly) and hosted by DigiDuncan, and for absolutely free.\n"
            "However, if you wish to contribute to DigiDuncan directly, you can do so here:\n"
            "https://donate.digiduncan.com\n"
            "SizeBot has been a passion project coded over a period of four years and learning a lot of Python along the way.\n"
            "Thank you so much for being here throughout this journey!")

    @commands.command(
        usage = "<message>",
        category = "misc"
    )
    async def bug(self, ctx, *, message: str):
        """Tell the devs there's an issue with SizeBot."""
        logger.warn(f"{ctx.author.id} ({ctx.author.name}) sent a bug report.")
        try:
            webhook = (await ctx.bot.get_channel(ids.sizebotbugreportschannel).webhooks())[0]
            await webhook.send(f"**Bug report** from <@{ctx.author.id}> in {ctx.guild.name}:\n> {message}\n{emojis.link}: https://discordapp.com/channels/{ctx.guild.id}/{ctx.channel.id}/{ctx.message.id}")
        except Forbidden:
            logger.error("I can't send webhooks in the bug reports channel!")

    @commands.command(
        usage = "<message>",
        category = "misc"
    )
    async def suggest(self, ctx, *, message: str):
        """Suggest a feature for SizeBot!"""
        logger.warn(f"{ctx.author.id} ({ctx.author.name}) sent a feature request.")
        try:
            webhook = (await ctx.bot.get_channel(ids.sizebotbugreportschannel).webhooks())[0]
            await webhook.send(f"**Feature request** from `{ctx.author}`:\n> {message}")
        except Forbidden:
            logger.error("I can't send webhooks in the bug reports channel!")

    @commands.command(
        aliases = ["objsuggest"],
        usage = "<message>",
        category = "misc"
    )
    async def suggestobject(self, ctx, *, message: str):
        """Suggest an object for SizeBot! (See help.)

        Suggest an object to be part of the lineup for commands like &natstats, &objcompare, and future fun!
        When suggesting an object, please give as many relavent measurements as you can.
        Things like, height, length, width, diameter, depth, and thickness, are all things SizeBot uses
        to make sure each object is a fun and exciting entry to pull up.
        Also include alternate names for the object, if it has them."""
        logger.warn(f"{ctx.author.id} ({ctx.author.name}) sent an object request.")
        try:
            webhook = (await ctx.bot.get_channel(ids.sizebotbugreportschannel).webhooks())[0]
            await webhook.send(f"**Object request** from `{ctx.author}`:\n> {message}")
        except Forbidden:
            logger.error("I can't send webhooks in the bug reports channel!")

    @commands.command(
        usage = ["[type]"],
        category = "help"
    )
    async def ping(self, ctx, subcommand: str = ""):
        """Pong!

        Check SizeBot's current latency.

        Check the bot's latency with `&ping`, or check the Discord API's latency with `&ping discord`."""
        waitMsg = await ctx.send(emojis.loading)

        if subcommand.lower() in ["heartbeat", "discord"]:
            response = f"Pong! :ping_pong:\nDiscord HEARTBEAT latency: {round(self.bot.latency, 3)} seconds"
        else:
            messageLatency = waitMsg.created_at - ctx.message.created_at
            response = f"Pong! :ping_pong:\nCommand latency: {utils.prettyTimeDelta(messageLatency.total_seconds(), True)}"
        await waitMsg.edit(content = response)

    @commands.command(
        category = "help"
    )
    async def changelog(self, ctx):
        """See what's new in the latest SizeBot!"""
        await ctx.send(f"View the changelog here!:\nhttps://github.com/sizedev/SizeBot3AndAHalf/blob/develop/changelogs/{__version__}.md")

    @commands.command(
        category = "mod"
    )
    @checks.is_mod()
    async def usercount(self, ctx):
        """How many users are registered?"""
        await ctx.send(f"There are **{userdb.countusers()}** users of SizeBot3½, with **{userdb.countprofiles()}** profiles created, <@!{ctx.message.author.id}>.")


class HelpCategory:
    def __init__(self, cid: str, name: str, description: str, emoji: str):
        self.cid = cid
        self.name = name
        self.description = description
        self.emoji = emoji


categories = [
    HelpCategory("help", "Help Commands", "Commands that help you.", "❓"),
    HelpCategory("setup", "Setup Commands", "Commands for setting up your SizeBot account.", "🧱"),
    HelpCategory("set", "Set Commands", "Commands for setting various stats.", "🖍️"),
    HelpCategory("setbase", "Set Base Commands", "Commands for setting various base stats.", "🖋️"),
    HelpCategory("change", "Change Commands", "Commands for changing your stats.", "📈"),
    HelpCategory("stats", "Stats Commands", "Commands for outputting yours and others stats.", "📊"),
    HelpCategory("scalestep", "Scale on Step Commands", "Commands related to scaling every step you take.", "🚶"),
    HelpCategory("profile", "Profile Commands", "Commands for updating and displaying profiles.", "🆔"),
    HelpCategory("fun", "Fun Commands", "Commands that aren't size-based, but are still fun!", "🎉"),
    HelpCategory("mod", "Mod Commands", "Commands for server mods.", "⚙️"),
    HelpCategory("misc", "Miscellaneous Commands", "Commands that defy category!", "🌐")
]


def setup(bot):
    bot.add_cog(HelpCog(bot))
