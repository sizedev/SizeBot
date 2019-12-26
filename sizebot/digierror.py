# import digiformatter as df


# error.message will be printed when you do print(error)
# error.user_message will be displayed to the user
class DigiException(Exception):
    def __init__(self, message, user_message = None, level = "warn"):
        if user_message is None:
            user_message = message
        self.delete_after = None
        self.user_message = user_message
        super().__init__(message)


class UserNotFoundException(DigiException):
    def __init__(self):
        message = f"User {userid} ({usernick}) not found."
        user_message = (f"Sorry, {usernick}! You aren't registered with SizeBot.\n"
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
        message = f"User {{userid}} tried to use {changemethod} change method."
        user_message = f"Sorry, {{usernick}}! {changemethod} is not a valid change method."
        super().__init__(message, user_message)


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
        super().__init__(message, level = "crit")
