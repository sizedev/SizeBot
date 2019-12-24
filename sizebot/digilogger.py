import sys
import traceback
import functools


# Error debugging
def print_error(command, error):
    print("Ignoring exception in command {}:".format(command), file = sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file = sys.stderr)


def err2console(func):
    @functools.wraps(func)
    async def func_wrapper(self, ctx, error):
        print_error(ctx.command, error)
        return await func(self, ctx, error)
    return func_wrapper
