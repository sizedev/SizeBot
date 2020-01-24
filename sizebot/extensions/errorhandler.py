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

        # If we got some bad arguments, use a generic argument exception error
        if isinstance(err, commands.BadUnionArgument) or isinstance(err, commands.MissingRequiredArgument):
            err = errors.ArgumentException(ctx)

        if isinstance(err, errors.AdminPermissionException):
            # Log Admin Permission Exceptions to telemetry
            telem = Telemetry.load()
            telem.incrementPermissionError(str(ctx.invoked_with))
            telem.save()

        if isinstance(err, errors.DigiContextException):
            # DigiContextException handling
            message = await err.formatMessage(ctx)
            if message is not None:
                logCmd = getattr(logger, err.level, logger.warn)
                await logCmd(message)
            userMessage = await err.formatUserMessage(ctx)
            if userMessage is not None:
                await ctx.send(userMessage)
        elif isinstance(err, errors.DigiException):
            # DigiException handling
            message = err.formatMessage()
            if message is not None:
                logCmd = getattr(logger, err.level, logger.warn)
                await logCmd(message)
            userMessage = err.formatUserMessage()
            if userMessage is not None:
                await ctx.send(userMessage)
        elif isinstance(err, commands.errors.CommandNotFound):
            # log unknown commmands to telemetry
            telem = Telemetry.load()
            telem.incrementUnknown(str(ctx.invoked_with))
            telem.save()
        else:
            # Default command error handling
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
            message = err.formatMessage()
            if message is not None:
                logCmd = getattr(logger, err.level, logger.warn)
                await logCmd(message)
        if isinstance(err, errors.DigiContextException):
            message = str(err)
            if message is not None:
                logCmd = getattr(logger, err.level, logger.warn)
                await logCmd(message)
        else:
            await logger.error(f"Ignoring exception in {event}")
            await logger.error(utils.formatTraceback(error))
