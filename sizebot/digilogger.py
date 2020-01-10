from discord.utils import escape_markdown

from sizebot import utils
from sizebot import digiformatter as df

logChannel = None


# Async log functions (prints to console, and logChannel if set)
async def trace(*args, **kwargs):
    await log("trace", *args, **kwargs)


async def debug(*args, **kwargs):
    await log("debug", *args, **kwargs)


async def info(*args, **kwargs):
    await log("info", *args, **kwargs)


async def warn(*args, **kwargs):
    await log("warn", *args, **kwargs)


async def error(*args, **kwargs):
    await log("error", *args, **kwargs)


async def log(level, msg, escapeMarkdown=True):
    msg = str(msg)
    print(df.formatLog(level, msg))
    if escapeMarkdown:
        escapedMsg = escape_markdown(msg)
    for m in utils.chunkMsg(escapedMsg, escapeMarkdown):
        await logChannel.send(m)


# Sync log functions (prints to console)
def synctrace(*args, **kwargs):
    synclog("trace", *args, **kwargs)


def syncdebug(*args, **kwargs):
    synclog("debug", *args, **kwargs)


def syncinfo(*args, **kwargs):
    synclog("info", *args, **kwargs)


def syncwarn(*args, **kwargs):
    synclog("warn", *args, **kwargs)


def syncerror(*args, **kwargs):
    synclog("error", *args, **kwargs)


def synclog(level, msg):
    msg = str(msg)
    print(df.formatLog(level, msg))


def init(channel):
    global logChannel
    logChannel = channel
