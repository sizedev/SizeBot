import logging


class CustomError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None


class ParseError(CustomError):
    pass


class DownloadError(ParseError):
    pass


class GametimeError(CustomError):
    pass


class OutOfPlayersError(GametimeError):
    pass


class OutOfEventsError(GametimeError):
    pass


class ThisShouldNeverHappenException(CustomError):
    level = logging.CRITICAL
