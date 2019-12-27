from sizebot import utils
from sizebot import digiformatter as df

logChannel = None


# Async log functions (prints to console, and logChannel if set)
async def trace(msg):
    await log("trace", msg)


async def debug(msg):
    await log("debug", msg)


async def info(msg):
    await log("info", msg)


async def warn(msg):
    await log("warn", msg)


async def error(msg):
    await log("error", msg)


async def log(level, msg):
    print(df.formatLog(level, msg))
    discordPrefix = "```\n"
    discordSuffix = "\n```"
    if logChannel is not None:
        msgMaxLen = 2000 - len(discordPrefix) - len(discordSuffix)
        for msgPart in utils.grouper(msgMaxLen, msg):
            await logChannel.send(f"```\n{msgPart}\n```")


# Sync log functions (prints to console)
def synctrace(msg):
    synclog("trace", msg)


def syncdebug(msg):
    synclog("debug", msg)


def syncinfo(msg):
    synclog("info", msg)


def syncwarn(msg):
    synclog("warn", msg)


def syncerror(msg):
    synclog("error", msg)


def synclog(level, msg):
    print(df.formatLog(level, msg))


def init(channel):
    global logChannel
    logChannel = channel
