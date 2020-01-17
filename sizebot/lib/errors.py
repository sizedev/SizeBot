

# error.message will be printed when you do print(error)
# error.user_message will be displayed to the user
class DigiException(Exception):
    __slots__ = ("message", "user_message", "level", "delete_after")

    def __init__(self, message = None, user_message = None, level = "warn", delete_after = None):
        self.message = message
        self.user_message = user_message
        self.level = level
        self.delete_after = None
        super().__init__(message)


class UserNotFoundException(DigiException):
    def __init__(self):
        message = "User {userid} ({usernick}) not found."
        user_message = ("Sorry, {usernick}! You aren't registered with SizeBot.\n"
                        "To register, use the `&register` command.")
        super().__init__(message, user_message)


class ValueIsZeroException(DigiException):
    def __init__(self):
        message = "Value zero received when unexpected."
        user_message = ("Nice try.\n"
                        "You can't change by a value of zero.")
        super().__init__(message, user_message)


class ValueIsOneException(DigiException):
    def __init__(self):
        message = "Value one received when unexpected."
        user_message = ("Nice try.\n"
                        "You can't change by a value of one.\n"
                        "The reason for this is that it doesn't do anything, "
                        "and this is a waste of memory and processing power for SizeBot, "
                        "especially if the task is a repeating one.")
        super().__init__(message, user_message)


class ChangeMethodInvalidException(DigiException):
    def __init__(self, changemethod):
        user_message = f"Sorry, {{usernick}}! {changemethod} is not a valid change method."
        super().__init__(user_message = user_message)


class CannotSaveWithoutIDException(DigiException):
    def __init__(self):
        message = "Tried to save a user without an ID."
        super().__init__(message, level = "crit")


class MessageWasDMException(DigiException):
    def __init__(self):
        message = "User {userid} tried to DM SizeBot."
        user_message = "Sorry, {usernick}! You can't DM SizeBot *(yet..!)*"
        super().__init__(message, user_message)


class NoPermissionsException(DigiException):
    def __init__(self):
        message = "SizeBot does not have the permssions to perform this action."
        super().__init__(message, level = "error")


class InvalidUserOrHeightException(DigiException):
    def __init__(self):
        user_message = "Sorry! I didn't recognize that user or height."
        super().__init__(user_message = user_message)


class InvalidUnitSystemException(DigiException):
    def __init__(self, unitsystem):
        user_message = f"{unitsystem!r} is an unrecognized unit system."
        super().__init__(user_message = user_message)


class InvalidSizeValue(DigiException):
    def __init__(self, sizevalue):
        user_message = f"{sizevalue!r} is an unrecognized size value."
        super().__init__(user_message = user_message)


class InvalidRollException(DigiException):
    def __init__(self, dString):
        user_message = f"Invalid roll string `{dString}`."
        super().__init__(user_message = user_message)


class AdminPermissionException(DigiException):
    def __init__(self):
        user_message = "{usernick} tried to run an admin command. This incident will be reported."  # TODO: Add this to telemetry.
        message = "{usernick} tried to run an admin command."
        super().__init__(message, user_message)


class ArgumentException(DigiException):
    def __init__(self, ctx):
        message = f"Please enter `{ctx.prefix}{ctx.invoked_with} {ctx.command.usage}`."
        super().__init__(message)
