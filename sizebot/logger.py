from digiformatter import logger

from sizebot.lib import utils

logChannel = None


# Async log functions (prints to console, and logChannel if set)
async def trace(message, **kwargs):
    await log(message, level="trace", **kwargs)


async def debug(message, **kwargs):
    await log(message, level="debug", **kwargs)


async def info(message, **kwargs):
    await log(message, level="info", **kwargs)


async def warn(message, **kwargs):
    await log(message, level="warn", **kwargs)


async def error(message, **kwargs):
    await log(message, level="error", **kwargs)


async def log(message, level="info"):
    message = str(message)
    logger.log(message, level=level)
    for m in utils.chunkMsg(message.replace("```", r"\`\`\`")):
        await logChannel.send(m)


# Sync log functions (prints to console)
def synctrace(message, **kwargs):
    synclog(message, level="trace", **kwargs)


def syncdebug(message, **kwargs):
    synclog(message, level="debug", **kwargs)


def syncinfo(message, **kwargs):
    synclog(message, level="info", **kwargs)


def syncwarn(message, **kwargs):
    synclog(message, level="warn", **kwargs)


def syncerror(message, **kwargs):
    synclog(message, level="error", **kwargs)


def synclog(message, level="info"):
    message = str(message)
    logger.log(message, level=level)


def init(channel):
    global logChannel
    logChannel = channel
