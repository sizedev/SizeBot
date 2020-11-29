from digiformatter import logger as digilogger

ROYALE = None


def create_log_levels():
    global ROYALE
    ROYALE = digilogger.addLogLevel("royale", fg="cyan")


create_log_levels()
