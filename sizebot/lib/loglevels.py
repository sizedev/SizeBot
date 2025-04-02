from typing import cast
from digiformatter import logger as digilogger

BANNER = cast(int, digilogger.addLogLevel("banner", fg="orange_red_1", bg="deep_sky_blue_4b", attr="bold", showtime = False))
LOGIN = cast(int, digilogger.addLogLevel("login", fg="cyan"))
EGG = cast(int, digilogger.addLogLevel("egg", fg="magenta_2b", bg="light_yellow", attr="bold", prefix="EGG"))
CMD = cast(int, digilogger.addLogLevel("cmd", fg="grey_50", base="DEBUG", prefix="CMD"))
ROYALE = cast(int, digilogger.addLogLevel("royale", fg="cyan", base="DEBUG", prefix="ROYALE"))
