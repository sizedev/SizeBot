import sys
import traceback
from datetime import datetime

import discord
from discord.ext import commands

from sizebot import digierror as errors
from sizebot import digilogger as logger
from sizebot import digiformatter as df
from sizebot.conf import conf


initial_extensions = [
    "sizebot.cogs.change",
    "sizebot.cogs.dm",
    "sizebot.cogs.fun",
    "sizebot.cogs.mod",
    "sizebot.cogs.monika",
    "sizebot.cogs.register",
    "sizebot.cogs.roll",
    "sizebot.cogs.set",
    "sizebot.cogs.stats",
    "sizebot.cogs.winks",
    "sizebot.cogs.banned",
    "sizebot.cogs.eval"
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
        if message.content.startswith("&") and message.content.endswith("&"):
            return  # Ignore Tupperboxes being mistaken for commands.
        await bot.process_commands(message)

    @bot.event
    async def on_command_error(ctx, error):
        # Get actual error
        err = getattr(error, "original", error)
        # DigiException handling
        if isinstance(err, errors.DigiException):
            if err.message is not None:
                log_message = err.message.format(usernick = ctx.message.author.display_name, userid = ctx.message.author.id)
                logCmd = getattr(logger, err.level, logger.warn)
                await logCmd(log_message)

            if err.user_message is not None:
                user_message = err.user_message.format(usernick = ctx.message.author.display_name, userid = ctx.message.author.id)
                await ctx.send(user_message, delete_after = err.delete_after)

            return

        if isinstance(err, commands.errors.MissingRequiredArgument):
            await ctx.send(str(err))
            return

        if isinstance(err, commands.errors.CommandNotFound):
            return

        # Default command handling
        await ctx.send("Something went wrong.")
        await logger.error(f"Ignoring exception in command {ctx.command}:")
        await logger.error("".join(traceback.format_exception(type(error), error, error.__traceback__)))

    @bot.event
    async def on_error(event, *args, **kwargs):
        (type, error, tb) = sys.exc_info()
        # Get actual error
        err = getattr(error, "original", error)
        # DigiException handling
        if isinstance(err, errors.DigiException):
            logCmd = getattr(logger, err.level, logger.warn)
            await logCmd(str(err))
            return

        await logger.error(f"Ignoring exception in {event}")
        await logger.error(traceback.format_exc())

    @bot.event
    async def on_disconnect():
        await logger.error("SizeBot has been disconnected from Discord!")

    if not conf.authtoken:
        logger.syncerror(f"Authentication token not found")
        return

    bot.run(conf.authtoken)


# Here we load our extensions(cogs) listed above in [initial_extensions].
if __name__ == "__main__":
    main()
