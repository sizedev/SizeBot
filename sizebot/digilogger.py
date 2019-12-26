import digiformatter as df


def trace(msg):
    df.log("trace", msg)


def debug(msg):
    df.log("debug", msg)


def info(msg):
    df.log("info", msg)


def warn(msg):
    df.log("warn", msg)


def error(msg):
    df.log("error", msg)
