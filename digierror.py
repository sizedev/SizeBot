import digiformatter as df


# error.message will be printed when you do print(error)
# error.user_message will be displayed to the user
class DigiException(Exception):
    def __init__(self, message):
        self.delete_after = None
        self.user_message = message
        super().__init__(message)


class UserNotFoundException(Exception):
    def __init__(self, userid):
        super().__init__(f"User {userid} not found.")
        self.user_message = ("Sorry! You aren't registered with SizeBot.\n"
                             "To register, use the `&register` command.")


SUCCESS = "success"
CHANGE_VALUE_IS_ZERO = "cvi0"
CHANGE_VALUE_IS_ONE = "cvi1"
CHANGE_METHOD_INVALID = "cmi"
CANNOT_SAVE_WITHOUT_ID = "cswi"


async def throw(ctx, code, delete=0):
    if code == SUCCESS:
        return
    if code == CHANGE_VALUE_IS_ZERO:
        df.warn(f"User {ctx.message.author.id} tried to change by zero.")
        await ctx.send("Nice try.\n"
                       "You can't change by zero. :stuck_out_tounge:", delete_after=delete)
    if code == CHANGE_VALUE_IS_ONE:
        df.warn(f"User {ctx.message.author.id} tried to change by one.")
        await ctx.send("You can't change by one.\n"
                       "This is because changing by one doesn't change the value of your attribute, and especially with slowchange tasks, this clogs up SizeBot's memory.", delete_after=delete)
    if code == CHANGE_METHOD_INVALID:
        df.warn(f"User {ctx.message.author.id} tried to use an invalid changing method.")
        await ctx.send("Your change method is invalid. Valid methods are add, subtract, multiply, or divide (and aliases for these modes.)", delete_after=delete)
    if code == CANNOT_SAVE_WITHOUT_ID:
        df.crit(f"Cannot save user without ID!")
        raise ValueError("Cannot save user without ID!")
