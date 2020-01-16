from datetime import datetime

import discord
from discord.ext import commands
from digiformatter import styles

from sizebot import __version__
from sizebot import digiSV, digiobj
from sizebot import digilogger as logger
from sizebot import conf
from sizebot import status

initial_extensions = [
    "sizebot.cogs.change",
    "sizebot.cogs.fun",
    "sizebot.cogs.help",
    "sizebot.cogs.monika",
    "sizebot.cogs.register",
    "sizebot.cogs.roll",
    "sizebot.cogs.set",
    "sizebot.cogs.stats",
    "sizebot.cogs.winks",
    "sizebot.cogs.banned",
    "sizebot.cogs.eval",
    "sizebot.cogs.errorhandler",
    "sizebot.cogs.admin",
    "sizebot.cogs.run",
    "sizebot.cogs.keypad"
]


def main():
    booting = True
    launchtime = datetime.now()

    bot = commands.Bot(command_prefix = conf.prefix, description = conf.description)

    bot.remove_command("help")
    for extension in initial_extensions:
        bot.load_extension(extension)

    async def on_first_ready():
        logChannel = bot.get_channel(conf.logchannelid)
        logger.init(logChannel)
        await digiSV.init()
        await digiobj.init()

        styles.create("banner", fg="orange_red_1", bg="deep_sky_blue_4b", attr="bold")
        styles.create("login", fg="cyan")
        # Obviously we need the banner printed in the terminal
        await logger.log(conf.banner + " v" + __version__, level="banner")
        await logger.log("Logged in as: {bot.user.name} ({bot.user.id})\n------", level="login")
        await bot.change_presence(activity = discord.Game(name = "Ratchet and Clank: Size Matters"))
        print(styles)
        launchfinishtime = datetime.now()
        elapsed = launchfinishtime - launchtime
        await logger.debug(f"SizeBot launched in {round((elapsed.total_seconds() * 1000), 3)} milliseconds.\n")
        status.ready()

    async def on_reconnect_ready():
        await logger.error("SizeBot has been reconnected to Discord.")

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
        # TODO: Move tupperbox to a check()
        # Ignore Tupperboxes being mistaken for commands.
        if message.content.startswith("&") and message.content.endswith("&"):
            return
        await bot.process_commands(message)

    @bot.event
    async def on_disconnect():
        logger.syncerror("SizeBot has been disconnected from Discord!")
        status.stopping()

    if not conf.authtoken:
        logger.syncerror(f"Authentication token not found!")
        return

    bot.run(conf.authtoken)


if __name__ == "__main__":
    main()
