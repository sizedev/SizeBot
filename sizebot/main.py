import logging
import sys
from datetime import datetime

import discord
from discord.ext.commands import Bot

from digiformatter import styles, logger as digilogger

from sizebot import __version__
from sizebot import conf
from sizebot import discordplus
from sizebot.cogs import edge, limits
from sizebot.lib import language, objs, proportions, status, units
from sizebot.lib.discordlogger import DiscordHandler
from sizebot.lib.loglevels import BANNER, LOGIN
from sizebot.plugins import active, monika

logging.basicConfig(level=logging.INFO)
dfhandler = digilogger.DigiFormatterHandler()

logger = logging.getLogger("sizebot")
logger.handlers = []
logger.propagate = False
logger.addHandler(dfhandler)

discordlogger = logging.getLogger("discord")
discordlogger.handlers = []
discordlogger.propagate = False
discordlogger.addHandler(dfhandler)

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
    "limits",
    "naptime",
    "profile",
    # "rainbow",
    "register",
    "roll",
    "run",
    "scalewalk",
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

discordplus.patch()


def main():
    try:
        conf.load()
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e.filename}")
        return

    booting = True
    launchtime = datetime.now()

    bot = Bot(command_prefix = conf.prefix, allowed_mentions = discord.AllowedMentions(everyone=False))

    bot.remove_command("help")

    for extension in initial_extensions:
        bot.load_extension("sizebot.extensions." + extension)
    for cog in initial_cogs:
        bot.load_extension("sizebot.cogs." + cog)

    async def on_first_ready():
        # Set up logging.
        logChannel = bot.get_channel(conf.logchannelid)
        discordhandler = DiscordHandler(logChannel)
        logger.addHandler(discordhandler)

        # Set the bots name to what's set in the config.
        try:
            await bot.user.edit(username = conf.name)
        except discord.errors.HTTPException:
            logger.warn("We can't change the username this much!")

        # Start the language engine.
        language.load()

        # Load the units and objects.
        await units.init()
        await objs.init()

        # Print the splash screen.
        # Obviously we need the banner printed in the terminal
        logger.log(BANNER, conf.banner + " v" + __version__)
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

    async def on_reconnect_ready():
        logger.error("SizeBot has been reconnected to Discord.")

    @bot.event
    async def on_ready():
        # Split on_ready into two events: one when we first boot, and one for reconnects.
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
        await limits.on_message(message)
        await proportions.nickUpdate(message.author)
        # await meicros.on_message(message)
        await monika.on_message(message)
        await active.on_message(message)

    @bot.event
    async def on_message_edit(before, after):
        if before.content == after.content:
            return
        await bot.process_commands(after)
        await proportions.nickUpdate(after.author)

    def on_disconnect():
        logger.error("SizeBot has been disconnected from Discord!")

    if not conf.authtoken:
        logger.error("Authentication token not found!")
        return

    bot.run(conf.authtoken)
    on_disconnect()


if __name__ == "__main__":
    main()
