from datetime import datetime
import logging

import discord
from discord.ext import commands
from digiformatter import styles, logger as digilogger

from sizebot import __version__
from sizebot import conf
from sizebot.lib import units, objs, status, discordlogger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sizebot")
logger.handlers = []
logger.propagate = False
logger.addHandler(digilogger.DigiFormatterHandler())

initial_cogs = [
    "admin",
    "change",
    "eval",
    "fun",
    "help",
    "keypad",
    "meicros",
    "monika",
    "register",
    "roll",
    "run",
    "set",
    "stats",
    "winks"
]
initial_extensions = [
    "banned",
    "errorhandler",
    "telemetry",
    "tupperbox"
]


def main():
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
        logger.addHandler(discordlogger.DiscordHandler(logChannel))

        await units.init()
        await objs.init()

        BANNER = digilogger.addLogLevel("banner", fg="orange_red_1", bg="deep_sky_blue_4b", attr="bold")
        LOGIN = digilogger.addLogLevel("login", fg="cyan")
        # Obviously we need the banner printed in the terminal
        logger.log(BANNER, conf.banner + " v" + __version__)
        logger.log(LOGIN, f"Logged in as: {bot.user.name} ({bot.user.id})\n------")
        await bot.change_presence(activity = discord.Game(name = "Ratchet and Clank: Size Matters"))
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

    @bot.event
    async def on_disconnect():
        logger.error("SizeBot has been disconnected from Discord!")
        status.stopping()

    if not conf.authtoken:
        logger.error(f"Authentication token not found!")
        return

    bot.run(conf.authtoken)


if __name__ == "__main__":
    main()
