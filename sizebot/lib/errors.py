from sizebot.lib import utils

# TODO: split this into DigiException and DigiContextException


# error.message will be printed when you do print(error)
# error.user_message will be displayed to the user
class DigiException(Exception):
    __slots__ = ()
    level = "warn"

    def formatMessage(self):
        return None

    def formatUserMessage(self):
        return None

    def __repr__(self):
        return utils.getFullname(self)

    def __str__(self):
        return self.formatMessage() or repr(self)


class DigiContextException(Exception):
    __slots__ = ()
    level = "warn"

    async def formatMessage(self, ctx):
        return None

    async def formatUserMessage(self, ctx):
        return None

    def __repr__(self):
        return utils.getFullname(self)

    def __str__(self):
        return repr(self)


class UserNotFoundException(DigiContextException):
    def __init__(self, userid):
        self.userid = userid

    async def formatMessage(self, ctx):
        user = await ctx.guild.fetch_member(self.userid)
        usernick = user.display_name
        return f"User {self.userid} ({usernick}) not found."

    async def formatUserMessage(self, ctx):
        user = await ctx.guild.fetch_member(self.userid)
        usernick = user.display_name
        return (
            f"Sorry, {usernick} isn't! You aren't registered with SizeBot.\n"
            "To register, use the `&register` command.")


class ValueIsZeroException(DigiException):
    def formatMessage(self):
        return "Value zero received when unexpected."

    def formatUserMessage(self):
        return (
            "Nice try.\n"
            "You can't change by a value of zero.")


class ValueIsOneException(DigiException):
    def formatMessage(self):
        return "Value one received when unexpected."

    def formatUserMessage(self):
        return (
            "Nice try.\n"
            "You can't change by a value of one.\n"
            "The reason for this is that it doesn't do anything, "
            "and this is a waste of memory and processing power for SizeBot, "
            "especially if the task is a repeating one.")


class ChangeMethodInvalidException(DigiContextException):
    def __init__(self, changemethod):
        self.changemethod = changemethod

    async def formatUserMessage(self, ctx):
        usernick = ctx.message.author.display_name
        return f"Sorry, {usernick}! {self.changemethod} is not a valid change method."


class CannotSaveWithoutIDException(DigiException):
    level = "crit"

    def formatMessage(self):
        return "Tried to save a user without an ID."


class NoPermissionsException(DigiException):
    level = "error"

    def formatMessage(self):
        "SizeBot does not have the permssions to perform this action."


# TODO: Unused
class InvalidUserOrHeightException(DigiException):
    def formatUserMessage(self):
        return "Sorry! I didn't recognize that user or height."


# TODO: Unused
class InvalidUnitSystemException(DigiException):
    def __init__(self, unitsystem):
        self.unitsystem = unitsystem

    def formatUserMessage(self):
        return f"{self.unitsystem!r} is an unrecognized unit system."


class InvalidSizeValue(DigiException):
    def __init__(self, sizevalue):
        self.sizevalue = sizevalue

    def formatUserMessage(self):
        return f"{self.sizevalue!r} is an unrecognized size value."


class InvalidRollException(DigiException):
    def __init__(self, dString):
        self.dString = dString

    def formatUserMessage(self):
        return f"Invalid roll string `{self.dString}`."


# TODO: Add this to telemetry.
class AdminPermissionException(DigiContextException):
    async def formatMessage(self, ctx):
        usernick = ctx.message.author.display_name
        return f"{usernick} tried to run an admin command."

    async def formatUserMessage(self, ctx):
        usernick = ctx.message.author.display_name
        return f"{usernick} tried to run an admin command. This incident will be reported."


class ArgumentException(DigiContextException):
    async def formatUserMessage(self, ctx):
        f"Please enter `{ctx.prefix}{ctx.invoked_with} {ctx.command.usage}`."
