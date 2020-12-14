import logging


class CustomError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        return f"{self.__name__}: {self.message}"


class ParseError(CustomError):
    pass


class DownloadError(ParseError):
    pass


class GametimeError(CustomError):
    pass


class OutOfPlayersError(GametimeError):
    def __init__(self, event):
        self.message = f"Out of players to run event {event}."


class OutOfEventsError(GametimeError):
    def __init__(self, round):
        self.message = f"Out of events to finish round {round}."


class ThisShouldNeverHappenException(CustomError):
    level = logging.CRITICAL
