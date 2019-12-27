from sizebot import digiformatter as df

logChannel = None


async def trace(msg):
    print(df.formatLog("trace", msg))
    if logChannel is not None:
        await logChannel.send(f"```\n{msg}\n```")


async def debug(msg):
    print(df.formatLog("debug", msg))
    if logChannel is not None:
        await logChannel.send(f"```\n{msg}\n```")


async def info(msg):
    print(df.formatLog("info", msg))
    if logChannel is not None:
        await logChannel.send(f"```\n{msg}\n```")


async def warn(msg):
    print(df.formatLog("warn", msg))
    if logChannel is not None:
        await logChannel.send(f"```\n{msg}\n```")


async def error(msg):
    print(df.formatLog("error", msg))
    if logChannel is not None:
        await logChannel.send(f"```\n{msg}\n```")


async def raw(msg):
    print(msg)


def syncError(msg):
    print(df.formatLog("error", msg))


def init(channel):
    global logChannel
    logChannel = channel
