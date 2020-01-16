import sys

from discord.ext import commands

from sizebot import logger
from sizebot.lib import errors, utils
from sizebot.lib.telemetry import Telemetry


def setup(bot):
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
            telem = Telemetry.load()
            telem.incrementUnknown(str(ctx.invoked_with))
            telem = telem.save()
            return

        # Default command handling
        await ctx.send("Something went wrong.")
        await logger.error(f"Ignoring exception in command {ctx.command}:")
        await logger.error(utils.formatTraceback(error))

    @bot.event
    async def on_error(event, *args, **kwargs):
        _, error, _ = sys.exc_info()
        # Get actual error
        err = getattr(error, "original", error)
        # DigiException handling
        if isinstance(err, errors.DigiException):
            logCmd = getattr(logger, err.level, logger.warn)
            await logCmd(str(err))
            return

        await logger.error(f"Ignoring exception in {event}")
        await logger.error(utils.formatTraceback(error))
