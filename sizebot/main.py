from datetime import datetime

import discord
from discord.ext import commands

from sizebot import digilogger as logger
from sizebot import digiformatter as df
from sizebot.conf import conf

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
    "sizebot.cogs.admin"
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

        df.createLogLevel("banner", fgval="orange_red_1", bgval="deep_sky_blue_4b", attrval="bold")
        df.createLogLevel("login", fgval="cyan")
        # Obviously we need the banner printed in the terminal
        await logger.log("banner", conf.banner + " v" + conf.version)

        await logger.log("login",
                         "Logged in as\n"
                         f"{bot.user.name}\n"
                         f"{bot.user.id}\n"
                         "------")
        await bot.change_presence(activity = discord.Game(name = "Ratchet and Clank: Size Matters"))
        df.printLogLevels()
        launchfinishtime = datetime.now()
        elapsed = launchfinishtime - launchtime
        await logger.debug(f"SizeBot launched in {round((elapsed.total_seconds() * 1000), 3)} milliseconds.\n")

    async def on_reconnect_ready():
        await logger.error("SizeBot has been reconected to Discord.")

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

    if not conf.authtoken:
        logger.syncerror(f"Authentication token not found")
        return

    bot.run(conf.authtoken)


if __name__ == "__main__":
    main()
