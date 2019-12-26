from sizebot import digiformatter as df


def trace(msg):
    print(df.formatLog("trace", msg))


def debug(msg):
    print(df.formatLog("debug", msg))


def info(msg):
    print(df.formatLog("info", msg))


def warn(msg):
    print(df.formatLog("warn", msg))


def error(msg):
    print(df.formatLog("error", msg))


def raw(msg):
    print(msg)
