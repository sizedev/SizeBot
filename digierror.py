import digiformatter as df


# error.message will be printed when you do print(error)
# error.user_message will be displayed to the user
class DigiException(Exception):
    def __init__(self, message, user_message = None):
        if user_message is None:
            user_message = message
        self.delete_after = None
        self.user_message = user_message
        super().__init__(message)


class UserNotFoundException(Exception):
    def __init__(self, userid):
        message = f"User {userid} not found."
        user_message = ("Sorry! You aren't registered with SizeBot.\n"
                        "To register, use the `&register` command.")
        super().__init__(message, user_message)


SUCCESS = "success"
USER_NOT_FOUND = "unf"
USER_IS_BOT = "uib"
USER_IS_WEBHOOK = "uiw"
USER_IS_OWNER = "uio"
CHANGE_VALUE_IS_ZERO = "cvi0"
CHANGE_VALUE_IS_ONE = "cvi1"
CHANGE_METHOD_INVALID = "cmi"
CANNOT_SAVE_WITHOUT_ID = "cswi"
MESSAGE_WAS_DM = "mwdm"
NO_PERMISSIONS = "np"


async def throw(code, **kwargs):
    delete = 0
    if 'delete' in kwargs:
        delete = kwargs['delete']

    if code == SUCCESS:
        return
    if code == USER_IS_BOT:
        pass
    if code == USER_IS_WEBHOOK:
        pass
    if code == USER_IS_OWNER:
        pass
    if code == USER_NOT_REGISTERED:
        pass
    if code == CHANGE_VALUE_IS_ZERO:
        df.warn(f"User {kwargs['ctx'].message.author.id} tried to change by zero.")
        await kwargs['ctx'].send("Nice try.\n"
                                 "You can't change by zero. :stuck_out_tounge:", delete_after=delete)
    if code == CHANGE_VALUE_IS_ONE:
        df.warn(f"User {kwargs['ctx'].message.author.id} tried to change by one.")
        await kwargs['ctx'].send("You can't change by one.\n"
                                 "This is because changing by one doesn't change the value of your attribute, and especially with slowchange tasks, this clogs up SizeBot's memory.", delete_after=delete)
    if code == CHANGE_METHOD_INVALID:
        df.warn(f"User {kwargs['ctx'].message.author.id} tried to use an invalid changing method.")
        await kwargs['ctx'].send("Your change method is invalid. Valid methods are add, subtract, multiply, or divide (and aliases for these modes.)", delete_after=delete)
    if code == CANNOT_SAVE_WITHOUT_ID:
        df.crit(f"Cannot save user without ID!")
        raise ValueError("Cannot save user without ID!")
    if code == MESSAGE_WAS_DM:
        df.warn(f"Tried to update user {kwargs['user'].id} ({kwargs['user'].name})'s nick, but the message was a DM (and hence there is no nickname to update.)")
    if code == NO_PERMISSIONS:
        df.crit("Missing permssions!")
