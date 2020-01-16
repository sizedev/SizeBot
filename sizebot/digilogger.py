from digiformatter import styles

from sizebot import utils

logChannel = None


# Async log functions (prints to console, and logChannel if set)
async def trace(message, **kwargs):
    log(message, level="trace", **kwargs)


async def debug(message, **kwargs):
    log(message, level="debug", **kwargs)


async def info(message, **kwargs):
    log(message, level="info", **kwargs)


async def warn(message, **kwargs):
    log(message, level="warn", **kwargs)


async def error(message, **kwargs):
    log(message, level="error", **kwargs)


async def log(message, level="info"):
    message = str(message)
    styles.print(message, style=level)
    for m in utils.chunkMsg(message.replace("```", r"\`\`\`")):
        await logChannel.send(m)


# Sync log functions (prints to console)
def synctrace(message, **kwargs):
    log(message, level="trace", **kwargs)


def syncdebug(message, **kwargs):
    log(message, level="debug", **kwargs)


def syncinfo(message, **kwargs):
    log(message, level="info", **kwargs)


def syncwarn(message, **kwargs):
    log(message, level="warn", **kwargs)


def syncerror(message, **kwargs):
    log(message, level="error", **kwargs)


def synclog(message, level="info"):
    message = str(message)
    styles.print(message, style=level)


def init(channel):
    global logChannel
    logChannel = channel
