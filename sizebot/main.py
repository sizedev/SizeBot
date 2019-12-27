import traceback
from datetime import datetime

from colored import fore, style, fg, bg
import discord
from discord.ext import commands

from sizebot import digierror as errors
from sizebot import digilogger as logger
from sizebot import digiformatter as df
from sizebot.conf import conf
from sizebot import utils


initial_extensions = [
    "sizebot.cogs.change",
    "sizebot.cogs.dm",
    "sizebot.cogs.fun",
    "sizebot.cogs.mod",
    "sizebot.cogs.monika",
    "sizebot.cogs.register",
    "sizebot.cogs.roleplay",
    "sizebot.cogs.set",
    "sizebot.cogs.stats",
    "sizebot.cogs.winks",
    "sizebot.cogs.banned"
]


def main():
    launchtime = datetime.now()

    bot = commands.Bot(command_prefix = conf.prefix, description = conf.description)

    bot.remove_command("help")
    for extension in initial_extensions:
        bot.load_extension(extension)

    @bot.event
    async def on_ready():
        logChannel = bot.get_channel(conf.logchannelid)
        logger.init(logChannel)

        # Obviously we need the banner printed in the terminal
        await logger.raw(bg(24) + fg(202) + style.BOLD + conf.banner + " v" + conf.version + style.RESET)

        await logger.raw(fore.CYAN + "Logged in as\n"
                         f"{bot.user.name}\n"
                         f"{bot.user.id}\n"
                         "------" + style.RESET)
        await bot.change_presence(activity = discord.Game(name = "Ratchet and Clank: Size Matters"))
        # list all log levels
        await logger.raw("log levels: " + (" ".join(df.formatLog(level, level, False) for level in df.loglevels.keys())))
        launchfinishtime = datetime.now()
        elapsed = launchfinishtime - launchtime
        await logger.debug(f"SizeBot launched in {round((elapsed.total_seconds() * 1000), 3)} milliseconds.\n")

    @bot.event
    async def on_message(message):
        if message.content.startswith("&") and message.content.endswith("&"):
            return  # Ignore Tupperboxes being mistaken for commands.
        utils.removeBrackets(message.content)
        await bot.process_commands(message)

    @bot.event
    async def on_command_error(ctx, error):
        # DigiException handling
        if isinstance(error, errors.DigiException):
            log_message = str(error).format(usernick = ctx.message.author.display_name, userid = ctx.message.author.id)
            logCmd = getattr(logger, error.level, logger.warn)
            logCmd(log_message)

            user_message = error.user_message.format(usernick = ctx.message.author.display_name, userid = ctx.message.author.id)
            await ctx.send(user_message, delete_after = error.delete_after)

            return

        # Default command handling
        await logger.error(f"Ignoring exception in command {ctx.command}:")
        await logger.error(traceback.format_exception(type(error), error, error.__traceback__))

    @bot.event
    async def on_error(event, *args, **kwargs):
        await logger.error(f"Ignoring exception in {event}")
        await logger.error(traceback.format_exc())

    @bot.event
    async def on_disconnect():
        await logger.error("SizeBot has been disconnected from Discord!")

    if not conf.authtoken:
        logger.syncError(f"Authentication token not found")
        return

    bot.run(conf.authtoken)


# Here we load our extensions(cogs) listed above in [initial_extensions].
if __name__ == "__main__":
    main()
