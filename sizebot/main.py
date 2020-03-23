import sys
from datetime import datetime
import logging

import discord
from discord.ext import commands
from digiformatter import styles, logger as digilogger

from sizebot import __version__
from sizebot import conf
from sizebot.lib import objs, status, units, proportions
from sizebot.plugins import monika, meicros
from sizebot.cogs import edge
from sizebot.lib.discordlogger import DiscordHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sizebot")
logger.handlers = []
logger.propagate = False
dfhandler = digilogger.DigiFormatterHandler()
logger.addHandler(dfhandler)

initial_cogs = [
    "admin",
    "change",
    "color",
    "edge",
    "eval",
    "fun",
    "help",
    "holiday",
    "keypad",
    "naptime",
    # "rainbow",
    "register",
    "roll",
    "run",
    "set",
    "stats",
    "test",
    "thistracker",
    "winks"
]
initial_extensions = [
    "banned",
    "errorhandler",
    "telemetry",
    "tupperbox"
]


def main():
    try:
        conf.load()
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e.filename}")
        return

    booting = True
    launchtime = datetime.now()

    bot = commands.Bot(command_prefix = conf.prefix, description = conf.description)

    bot.remove_command("help")

    for extension in initial_extensions:
        bot.load_extension("sizebot.extensions." + extension)
    for cog in initial_cogs:
        bot.load_extension("sizebot.cogs." + cog)

    async def on_first_ready():
        logChannel = bot.get_channel(conf.logchannelid)
        discordhandler = DiscordHandler(logChannel)
        logger.addHandler(discordhandler)
        discordlogger = logging.getLogger("discord")
        discordlogger.addHandler(discordhandler)

        await units.init()
        await objs.init()

        BANNER = digilogger.addLogLevel("banner", fg="orange_red_1", bg="deep_sky_blue_4b", attr="bold")
        LOGIN = digilogger.addLogLevel("login", fg="cyan")
        # Obviously we need the banner printed in the terminal
        logger.log(BANNER, conf.banner + " v" + __version__)
        logger.log(LOGIN, f"Logged in as: {bot.user.name} ({bot.user.id})\n------")

        # Add a special message to bot status if we are running in debug mode
        activity = discord.Game(name = "Ratchet and Clank: Size Matters")
        if sys.gettrace() is not None:
            activity = discord.Activity(type=discord.ActivityType.listening, name = "DEBUGGER 🔧")

        await bot.change_presence(activity = activity)
        print(styles)
        logger.info(f"Prefix: {conf.prefix}")
        launchfinishtime = datetime.now()
        elapsed = launchfinishtime - launchtime
        logger.debug(f"SizeBot launched in {round((elapsed.total_seconds() * 1000), 3)} milliseconds.\n")
        status.ready()

    async def on_reconnect_ready():
        logger.error("SizeBot has been reconnected to Discord.")

    @bot.event
    async def on_ready():
        nonlocal booting
        if booting:
            await on_first_ready()
            booting = False
        else:
            await on_reconnect_ready()

    @bot.event
    async def on_message(message):
        await bot.process_commands(message)
        await edge.on_message(message)
        await proportions.nickUpdate(message.author)
        await meicros.on_message(message)
        await monika.on_message(message)

    @bot.event
    async def on_message_edit(before, after):
        if before.content == after.content:
            return
        await bot.process_commands(after)
        await proportions.nickUpdate(after.author)

    @bot.event
    async def on_disconnect():
        logger.error("SizeBot has been disconnected from Discord!")

    if not conf.authtoken:
        logger.error(f"Authentication token not found!")
        return

    bot.run(conf.authtoken)


if __name__ == "__main__":
    main()
