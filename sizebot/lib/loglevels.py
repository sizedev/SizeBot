from digiformatter import logger as digilogger

BANNER = None
LOGIN = None
EGG = None


def create_log_levels():
    global BANNER, LOGIN, EGG
    BANNER = digilogger.addLogLevel("banner", fg="orange_red_1", bg="deep_sky_blue_4b", attr="bold")
    LOGIN = digilogger.addLogLevel("login", fg="cyan")
    EGG = digilogger.addLogLevel("egg", fg="magenta_2b", bg="light_yellow", attr="bold")


create_log_levels()
