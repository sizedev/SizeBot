import sys
import traceback
import functools
import time
from time import strftime, localtime

# Error debugging
def print_error(command, error):
    print('Ignoring exception in command {}:'.format(command), file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

def err2console(func):
    @functools.wraps(func)
    async def func_wrapper(self, ctx, error):
        print_error(ctx.command, error)
        return await func(self, ctx, error)
    return func_wrapper

#Color styling for terminal messages.
def time():
	return (fore.MAGENTA + strftime("%d %b %H:%M:%S | ", localtime()) + style.RESET)
def warn(message):
	print(time() + fore.YELLOW + message + style.RESET)
def crit(message):
	print(time() + back.RED + style.BOLD + message + style.RESET)
def test(message):
	print(time() + fore.BLUE + message + style.RESET)
def msg(message):
	 print(time() + fg(51) + message + style.RESET)
def load(message):
		return (fg(238) + message + style.RESET)
