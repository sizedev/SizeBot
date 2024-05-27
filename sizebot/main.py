import arrow
import os
import logging
import pytz
import sys
from datetime import datetime, timedelta

import discord
from discord.ext.commands import Bot

from digiformatter import styles, logger as digilogger

import discordplus

from sizebot import __version__
from sizebot.conf import conf
from sizebot.lib import language, objs, paths, pokemon, status, units, utils, nickmanager
from sizebot.lib.discordlogger import DiscordHandler
from sizebot.lib.loglevels import BANNER, LOGIN, CMD
from sizebot.lib.types import BotContext
from sizebot.lib.utils import truncate
from sizebot.plugins import active, monika

logging.basicConfig(level=CMD)
dfhandler = digilogger.DigiFormatterHandler()
dfhandler.setLevel(CMD)

logger = logging.getLogger("sizebot")
logger.setLevel(CMD)
logger.handlers = []
logger.propagate = False
logger.addHandler(dfhandler)

discordlogger = logging.getLogger("discord")
discordlogger.setLevel(logging.WARNING)
discordlogger.handlers = []
discordlogger.propagate = False
discordlogger.addHandler(dfhandler)

initial_cogs = [
    "admin",
    "change",
    "edge",
    "eval",
    "fun",
    "help",
    "holiday",
    "keypad",
    "limits",
    "loop",
    "multiplayer",
    "naptime",
    "objects",
    "pokemon",
    "profile",
    "quake",
    "register",
    "roll",
    "say",
    "scaletalk",
    "scalewalk",
    "set",
    "setbase",
    "stats",
    "test",
    "thistracker",
    "trigger",
    "weird",
    "winks"
]
initial_extensions = [
    "banned",
    "errorhandler",
    "tupperbox"
]

discordplus.patch()


# TODO: CamelCase
def initConf():
    print("Initializing configuration file")
    try:
        conf.init()
        print(f"Configuration file initialized: {paths.confpath}")
    except FileExistsError as e:
        print(e)
        pass
    os.startfile(paths.confpath.parent)


def main():
    try:
        conf.load()
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e.filename}")
        return

    launchtime = datetime.now()

    bot = Bot(command_prefix = conf.prefix, allowed_mentions = discord.AllowedMentions(everyone=False), intents=discord.Intents.all(), case_insensitive=True)

    bot.remove_command("help")

    # Start the language engine.
    language.load()

    # Load the units and objects.
    units.init()
    objs.init()
    pokemon.init()

    @bot.event
    async def setup_hook():
        logger.info("Setup hook called!")
        for extension in initial_extensions:
            await bot.load_extension("sizebot.extensions." + extension)
        for cog in initial_cogs:
            await bot.load_extension("sizebot.cogs." + cog)
        # await bot.load_extension("sizeroyale.cogs.royale")

    @bot.event
    async def on_first_ready():
        # Set up logging.
        if conf.logchannelid:
            logChannel = bot.get_channel(conf.logchannelid)
            discordhandler = DiscordHandler(logChannel)
            discordhandler.setLevel(logging.INFO)
            logger.addHandler(discordhandler)

        # Set the bots name to what's set in the config.
        try:
            await bot.user.edit(username = conf.name)
        except discord.errors.HTTPException:
            logger.warn("We can't change the username this much!")

        # Print the splash screen.
        # Obviously we need the banner printed in the terminal
        banner = (
            R"   _____ _         ____        _   ____   _____ ""\n"
            R"  / ____(_)       |  _ \      | | |___ \ | ____|""\n"
            R" | (___  _ _______| |_) | ___ | |_  __) || |__  ""\n"
            R"  \___ \| |_  / _ \  _ < / _ \| __||__ < |___ \ ""\n"
            R"  ____) | |/ /  __/ |_) | (_) | |_ ___) | ___) |""\n"
            R" |_____/|_/___\___|____/ \___/ \__|____(_)____/ ""\n"
            R"                                                ""\n"
            R"                                                 v" + __version__)
        logger.log(BANNER, banner)
        logger.log(LOGIN, f"Logged in as: {bot.user.name} ({bot.user.id})\n------")

        # Add a special message to bot status if we are running in debug mode
        activity = discord.Game(name = "Ratchet and Clank: Size Matters")
        if sys.gettrace() is not None:
            activity = discord.Activity(type=discord.ActivityType.listening, name = "DEBUGGER 🔧")

        # More splash screen.
        await bot.change_presence(activity = activity)
        print(styles)
        logger.info(f"Prefix: {conf.prefix}")
        launchfinishtime = datetime.now()
        elapsed = launchfinishtime - launchtime
        logger.debug(f"SizeBot launched in {round((elapsed.total_seconds() * 1000), 3)} milliseconds.\n")
        status.ready()

    @bot.event
    async def on_reconnect_ready():
        logger.error("SizeBot has been reconnected to Discord.")

    @bot.event
    async def on_command(ctx: BotContext):
        guild = truncate(ctx.guild.name, 20) if (hasattr(ctx, "guild") and ctx.guild is not None) else "DM"
        logger.log(CMD, f"G {guild}, U {ctx.message.author.name}: {ctx.message.content}")

    @bot.event
    async def on_message(message: discord.Message):
        # F*** smart quotes.
        message.content = message.content.replace("“", "\"")
        message.content = message.content.replace("”", "\"")
        message.content = message.content.replace("’", "'")
        message.content = message.content.replace("‘", "'")

        if (
            message.content.startswith(f"{conf.prefix}timeit")
            and await bot.is_owner(message.author)
            and hasattr(message.author, "guild") and message.author.guild is not None
        ):
            await on_message_timed(message)
            return
        await bot.process_commands(message)

        if hasattr(message.author, "guild") and message.author.guild is not None:
            await nickmanager.nick_update(message.author)
        await monika.on_message(message)
        await active.on_message(message)

    async def on_message_timed(message: discord.Message):
        def timeywimey() -> timedelta:
            now = arrow.now()
            if getattr(timeywimey, "prev", None) is None:
                timeywimey.prev = now
            prev: arrow.Arrow = timeywimey.prev
            diff = now - prev
            timeywimey.prev = now
            return diff

        message.content = message.content[len(conf.prefix + "timeit"):].lstrip()
        start = arrow.get(message.created_at.replace(tzinfo=pytz.UTC))
        discordlatency = arrow.now() - start
        timeywimey()
        await bot.process_commands(message)
        processlatency = timeywimey()
        await nickmanager.nick_update(message.author)
        nickupdatelatency = timeywimey()
        await monika.on_message(message)
        monikalatency = timeywimey()
        await active.on_message(message)
        activelatency = timeywimey()
        end = arrow.now()
        totaltime = end - start

        latency = (
            f"Discord Latency: {utils.pretty_time_delta(discordlatency.total_seconds(), True)}\n"
            f"Command Process Latency: {utils.pretty_time_delta(processlatency.total_seconds(), True)}\n"
            f"Nick Update Latency: {utils.pretty_time_delta(nickupdatelatency.total_seconds(), True)}\n"
            f"Monika Latency: {utils.pretty_time_delta(monikalatency.total_seconds(), True)}\n"
            f"User Active Check Latency: {utils.pretty_time_delta(activelatency.total_seconds(), True)}\n"
            f"**Total Latency: {utils.pretty_time_delta(totaltime.total_seconds(), True)}**"
        )
        await message.channel.send(latency)

    @bot.event
    async def on_message_edit(before: discord.Message, after: discord.Message):
        if before.content == after.content:
            return
        await bot.process_commands(after)
        if hasattr(after.author, "guild") and after.author.guild is not None:
            await nickmanager.nick_update(after.author)
        await active.on_message(after)

    @bot.event
    async def on_guild_join(guild: discord.Guild):
        with open(paths.blacklistpath) as f:
            blacklist = [int(line) for line in f.readlines()]

        if guild.id in blacklist:
            await guild.owner.send("SizeBot is not available for this server.")

            logger.error(f"SizeBot tried to be added to {guild.name}! ({guild.id}), but it was in the blacklist!")
            await guild.leave()
            return

        logger.warn(f"SizeBot has been added to {guild.name}! ({guild.id})\n"
                    f"You should talk to the owner, {guild.owner}! ({guild.owner.id})")

    @bot.event
    async def on_guild_remove(guild: discord.Guild):
        logger.warn(f"SizeBot has been removed from {guild.name}! ({guild.id})")

    def on_disconnect():
        logger.error("SizeBot has been disconnected from Discord!")

    if not conf.authtoken:
        logger.error("Authentication token not found!")
        return

    bot.run(conf.authtoken)
    on_disconnect()


if __name__ == "__main__":
    main()
