import aiohttp
import logging
import math

from datetime import datetime
from packaging import version

from discord import Embed, Webhook
from discord.ext import commands

from sizebot import __version__
from sizebot.conf import conf
from sizebot.lib import checks, userdb, utils
from sizebot.lib.constants import colors, emojis
from sizebot.lib.menu import Menu
from sizebot.lib.stats import statmap
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

alpha_warning = f"{emojis.warning} **This command is in ALPHA.** It may break, be borked, change randomly, be removed randomly, or be deprecated at any time. Proceed with caution."
accuracy_warning = f"{emojis.warning} **This command may not be entirely accurate.** It makes assumptions and guesses that have a decent amount of wiggle room, even because the information isn't known or because the calculations are meant to be for fiction only. Don't take these results at face value!"
stats_string = utils.sentence_join([f"`{v}`" for v in statmap.keys()])


async def post_report(report_type, message, report_text):
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(conf.bugwebhookurl, session = session)
        guild_name = "DM" if not message.channel.guild else message.channel.guild.name
        await webhook.send(
            f"**{report_type}** from <@{message.author.id}> in {guild_name}:\n"
            f"> {report_text}\n"
            f"{message.jump_url} {emojis.link}",
            files=[await a.to_file() for a in message.attachments]
        )


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
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        category = "help"
    )
    async def units(self, ctx: commands.Context):
        """Get a list of the various units SizeBot accepts."""
        heightobjectunits = [su.unit for su in SV._systems["o"]._systemunits]
        weightobjectunits = [su.unit for su in WV._systems["o"]._systemunits]

        heightunits = [str(u) for u in sorted(SV._units) if u not in heightobjectunits]
        weightunits = [str(u) for u in sorted(WV._units) if u not in weightobjectunits]

        embed = Embed(title=f"Units [SizeBot {__version__}]")

        for n, units in enumerate(utils.chunk_list(heightunits, math.ceil(len(heightunits) / 3))):
            embed.add_field(name="Height" if n == 0 else "\u200b", value="\n".join(units))

        for n, units in enumerate(utils.chunk_list(weightunits, math.ceil(len(weightunits) / 3))):
            embed.add_field(name="Weight" if n == 0 else "\u200b", value="\n".join(units))

        await ctx.send(embed=embed)

    async def send_summary_help(self, ctx: commands.Context):
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
        embed.set_author(name = f"requested by {ctx.author.name}", icon_url = ctx.author.avatar)

        # Add each category to a field
        for cat in categories:
            cat_cmds = commands_by_cat.get(cat.cid, [])
            if not cat_cmds:
                # logger.warn(f"Command category {cat.cid!r} is empty.")
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

    async def send_category_help(self, ctx: commands.Context, category, cmds):
        # Prepare the embed for the category
        embed = Embed(title=f"{category.name} Help [SizeBot {__version__}]")
        embed.set_author(name = ctx.author.name, icon_url = ctx.author.avatar)

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

    async def send_command_help(self, ctx: commands.Context, cmd):
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
        description += "\n\n".join(descriptionParts).replace("&", ctx.prefix).replace("#STATS#", stats_string).replace("#ALPHA#", alpha_warning).replace("#ACC#", accuracy_warning)

        embed = Embed(
            title=signature,
            description=description
        ).set_author(name=f"Help [SizeBot {__version__}]").set_footer(text=f"See `{conf.prefix}help <command>` for more details about a command and how to use it.")

        if cmd.aliases:
            embed.add_field(name="**Aliases:**", value=", ".join(cmd.aliases), inline=False)

        await ctx.send(embed=embed)

    @commands.command(
        description="[description]",
        usage="[usage]",
        aliases=["helpme", "wtf", "commands", "cmds"],
        category = "help"
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def help(self, ctx: commands.Context, cmdName: str = None):
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
    async def about(self, ctx: commands.Context):
        """Get the credits and some facts about SizeBot."""
        now = datetime.now()
        embed = Embed(title = "SizeBot3½", description = "Credits", color = colors.cyan)
        embed.set_author(name = "DigiDuncan")
        embed.set_image(url = "https://cdn.discordapp.com/attachments/650460192009617433/698529527965417552/sizebotlogot.png")
        embed.add_field(name = "Credits",
                        value = ("**Coding Assistance** *by Natalie*\n"
                                 "**Additional Equations** *by Benyovski, Arceus3251 and DragonMoffon*\n"
                                 "**Originally Tested** *by Aria, Kelly, worstgender, and Arceus3251*\n"),
                        inline = False)
        embed.add_field(name = "Technical Details",
                        value = "Written in Python 3.6, and slowly upgraded to 3.12. Written Visual Studio Code. External libraries used are `discord.py` (rewrite version), `digiformatter` (my personal terminal-formatting library), and various dependencies you can find on the GitHub page.",
                        inline = False)
        embed.add_field(name = "Server",
                        value = "Go to this server: https://discord.gg/bbGjN8dTgk for help with the bot!",
                        inline = False)
        embed.set_footer(text = f"Version {__version__} | {now.strftime('%d %b %Y')}")
        await ctx.send(embed = embed)

    @commands.command(
        aliases = ["fund"],
        category = "help"
    )
    async def donate(self, ctx: commands.Context):
        """Give some monetary love to your favorite bot developer!"""
        await ctx.send(
            f"<@{ctx.author.id}>\n"
            "SizeBot is coded (mainly) and hosted by DigiDuncan, and for absolutely free.\n"
            "However, if you wish to contribute to DigiDuncan directly, you can do so here:\n"
            "<https://paypal.me/DigiDuncanPayPal>\n"
            "SizeBot has been a passion project coded over a period of four years and learning a lot of Python along the way.\n"
            "Thank you so much for being here throughout this journey!")

    @commands.command(
        usage = "<message>",
        category = "misc",
        multiline = True
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def bug(self, ctx: commands.Context, *, message: str):
        """Tell the devs there's an issue with SizeBot."""
        logger.warn(f"{ctx.author.id} ({ctx.author.name}) sent a bug report.")
        await post_report("Bug report", ctx.message, message)
        await ctx.send("Bug report sent.")

    @commands.command(
        usage = "<message>",
        category = "misc",
        multiline = True
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def suggest(self, ctx: commands.Context, *, message: str):
        """Suggest a feature for SizeBot!"""
        logger.warn(f"{ctx.author.id} ({ctx.author.name}) sent a feature request.")
        await post_report("Feature request", ctx.message, message)
        await ctx.send("Feature request sent.")
        if any(nonoword in message for nonoword in ["weiner", "wiener", "penis", "dick", "boob", "vagina", "pussy", "breast", "cock", "nsfw"]):
            await ctx.send("<:LEWD:625464094157439010>")

    @commands.command(
        aliases = ["objsuggest"],
        usage = "<message>",
        category = "misc",
        multiline = True
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def suggestobject(self, ctx: commands.Context, *, message: str):
        """Suggest an object for SizeBot! (See help.)

        Suggest an object to be part of the lineup for commands like &natstats, &objcompare, and future fun!
        When suggesting an object, please give as many relavent measurements as you can.
        Things like, height, length, width, diameter, depth, and thickness, are all things SizeBot uses
        to make sure each object is a fun and exciting entry to pull up.
        Also include alternate names for the object, if it has them."""
        logger.warn(f"{ctx.author.id} ({ctx.author.name}) sent an object request.")
        await post_report("Object request", ctx.message, message)
        await ctx.send("Object suggestion sent.")

    @commands.command(
        usage = ["[type]"],
        category = "help"
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ping(self, ctx: commands.Context, subcommand: str = ""):
        """Pong!

        Check SizeBot's current latency.

        Check the bot's latency with `&ping`, or check the Discord API's latency with `&ping discord`."""
        waitMsg = await ctx.send(emojis.loading)

        if subcommand.lower() in ["heartbeat", "discord"]:
            response = f"Pong! :ping_pong:\nDiscord HEARTBEAT latency: {round(self.bot.latency, 3)} seconds"
        else:
            messageLatency = waitMsg.created_at - ctx.message.created_at
            response = f"Pong! :ping_pong:\nCommand latency: {utils.pretty_time_delta(messageLatency.total_seconds(), True)}"
        await waitMsg.edit(content = response)

    @commands.command(
        usage = ["[type]"],
        category = "help",
        hidden = True
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pong(self, ctx: commands.Context, subcommand: str = ""):
        """Ping!"""
        waitMsg = await ctx.send(emojis.loading)

        if subcommand.lower() in ["heartbeat", "discord"]:
            response = f"Ping! :ping_pong:\nDiscord HEARTBEAT latency: -{round(self.bot.latency, 3)} seconds"
        else:
            messageLatency = waitMsg.created_at - ctx.message.created_at
            response = f"Ping! :ping_pong:\nCommand latency: -{utils.pretty_time_delta(messageLatency.total_seconds(), True)}"
        await waitMsg.edit(content = response)

    @commands.command(
        category = "help"
    )
    async def changelog(self, ctx: commands.Context):
        """See what's new in the latest SizeBot!"""
        current_version = version.parse(__version__)

        await ctx.send(f"View the changelog here!:\nhttps://github.com/sizedev/SizeBot/blob/master/changelogs/{current_version.major}.{current_version.minor}.md")

    @commands.command(
        category = "mod",
        hidden = True
    )
    @checks.is_mod()
    async def usercount(self, ctx: commands.Context):
        """How many users are registered?"""
        await ctx.send(f"There are **{userdb.count_users()}** users of SizeBot3½, with **{userdb.count_profiles()}** profiles created, <@!{ctx.message.author.id}>.")

    @commands.command(
        category = "help"
    )
    async def invite(self, ctx: commands.Context):
        """Request an invite for SizeBot!"""
        await ctx.send("## Thank you for the interest in the bot!\n"
                       "You can invite SizeBot to your server now!\n"
                       f"- Use this [link](https://discord.com/oauth2/authorize?client_id={ctx.bot.application_id}&permissions=563365424786496&scope=bot) to invite SizeBot to your server!\n"
                       f"- (Use this [link](https://discord.com/oauth2/authorize?client_id={ctx.bot.application_id}&permissions=0&scope=bot) if you would like to manually manage the bot permissions).\n"
                       "If you need help, reach out to DigiDuncan (@digiduncan) and use `&help`! You can also go to this server for additional help: https://discord.gg/bbGjN8dTgk")


class HelpCategory:
    def __init__(self, cid: str, name: str, description: str, emoji: str):
        self.cid = cid
        self.name = name
        self.description = description
        self.emoji = emoji


# Do not add more than 19 of these!
categories = [
    HelpCategory("help", "Help Commands", "Commands that help you.", "❓"),
    HelpCategory("setup", "Setup Commands", "Commands for setting up your SizeBot account.", "🧱"),
    HelpCategory("set", "Set Commands", "Commands for setting various stats.", "🖍️"),
    HelpCategory("setbase", "Set Base Commands", "Commands for setting various base stats.", "🖋️"),
    HelpCategory("change", "Change Commands", "Commands for changing your stats.", "📈"),
    HelpCategory("stats", "Stats Commands", "Commands for outputting yours and others stats.", "📊"),
    HelpCategory("objects", "Objects Commands", "Commands about objects and comparing to them.", "💎"),
    HelpCategory("scalestep", "Scale on Action Commands", "Commands related to scaling every action you take.", "🚶"),
    HelpCategory("trigger", "Trigger Commands", "Commands related to trigger words.", "🔫"),
    HelpCategory("loop", "Looping Commands", "Commands related to doing looping tasks.", "🔁"),
    HelpCategory("multiplayer", "Multiplayer Commands", "Commands for playing with others.", "👥"),
    HelpCategory("profile", "Profile Commands", "Commands for updating and displaying profiles.", "🆔"),
    HelpCategory("fun", "Fun Commands", "Commands that are fun!", "🎉"),
    HelpCategory("mod", "Mod Commands", "Commands for server mods.", "⚙️"),
    HelpCategory("misc", "Miscellaneous Commands", "Commands that defy category!", "🌐")
]


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
