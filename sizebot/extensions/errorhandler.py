import logging
import sys

from discord.ext import commands

from sizebot.lib import errors, utils
from sizebot.lib.telemetry import Telemetry

logger = logging.getLogger("sizebot")


def setup(bot):
    @bot.event
    async def on_command_error(ctx, error):
        # Get actual error
        err = getattr(error, "original", error)

        # If we got some bad arguments, use a generic argument exception error
        if isinstance(err, commands.BadUnionArgument) or isinstance(err, commands.MissingRequiredArgument) or isinstance(err, commands.BadArgument):
            err = errors.ArgumentException()

        if isinstance(err, commands.NotOwner):
            err = errors.AdminPermissionException()

        if isinstance(err, errors.AdminPermissionException):
            # Log Admin Permission Exceptions to telemetry
            telem = Telemetry.load()
            telem.incrementPermissionError(str(ctx.invoked_with))
            telem.save()

        if isinstance(err, errors.DigiContextException):
            # DigiContextException handling
            message = await err.formatMessage(ctx)
            if message is not None:
                logger.log(err.level, message)
            userMessage = await err.formatUserMessage(ctx)
            if userMessage is not None:
                await ctx.send(userMessage)
        elif isinstance(err, errors.DigiException):
            # DigiException handling
            message = err.formatMessage()
            if message is not None:
                logger.log(err.level, message)
            userMessage = err.formatUserMessage()
            if userMessage is not None:
                await ctx.send(userMessage)
        elif isinstance(err, commands.errors.CommandNotFound):
            # log unknown commmands to telemetry
            telem = Telemetry.load()
            telem.incrementUnknown(str(ctx.invoked_with))
            telem.save()
        elif isinstance(err, commands.errors.ExpectedClosingQuoteError):
            await ctx.send("Mismatched quotes in command.")
        elif isinstance(err, commands.errors.InvalidEndOfQuotedStringError):
            await ctx.send("No space after a quote in command. Are your arguments smushed together?")
        else:
            # Default command error handling
            await ctx.send("Something went wrong.")
            logger.error(f"Ignoring exception in command {ctx.command}:")
            logger.error(utils.formatTraceback(error))

    @bot.event
    async def on_error(event, *args, **kwargs):
        _, error, _ = sys.exc_info()
        # Get actual error
        err = getattr(error, "original", error)
        # DigiException handling
        if isinstance(err, errors.DigiException):
            message = err.formatMessage()
            if message is not None:
                logger.log(err.level, message)
        if isinstance(err, errors.DigiContextException):
            message = str(err)
            if message is not None:
                logger.log(err.level, message)
        else:
            logger.error(f"Ignoring exception in {event}")
            logger.error(utils.formatTraceback(error))
