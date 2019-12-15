import sys
import traceback
from datetime import datetime

from colored import fore, style, fg, bg
import discord
from discord.ext import commands

import digierror as errors
import digiformatter as df
from globalsb import banner, version, check, allowbrackets, removeBrackets

launchtime = datetime.now()

# Get authtoken from file.
with open("../_authtoken.txt") as f:
    authtoken = f.readlines()
authtoken = [x.strip() for x in authtoken]
authtoken = authtoken[0]

# Predefined variables.
prefix = '&'
description = '''SizeBot3 is a complete rewrite of SizeBot for the Macropolis and, later, Size Matters server.
SizeBot3AndAHalf is a refactorization for SB3 and adds database support.
Written by DigiDuncan.
The SizeBot Team: DigiDuncan, Natalie, Kelly, AWK_, Benyovski, Arceus3521, Surge The Raichu.'''
initial_extensions = [
    'cogs.change',
    'cogs.dm',
    'cogs.fun',
    'cogs.mod',
    'cogs.monika',
    'cogs.register',
    'cogs.roleplay',
    'cogs.set',
    'cogs.stats',
    'cogs.winks'
]

# Obviously we need the banner printed in the terminal.
print(bg(24) + fg(202) + style.BOLD + banner + style.RESET + " v" + version)

bot = commands.Bot(command_prefix=prefix, description=description)
bot.remove_command("help")
bot.add_check(check)


# Output header
@bot.event
async def on_ready():
    print(fore.CYAN + 'Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------' + style.RESET)
    await bot.change_presence(activity=discord.Game(name="Ratchet and Clank: Size Matters"))
    df.warn("Warn test.")
    df.crit("Crit test.")
    df.test("Test test.")
    launchfinishtime = datetime.now()
    elapsed = launchfinishtime - launchtime
    df.test(f"SizeBot launched in {round((elapsed.total_seconds() * 1000), 3)} milliseconds.")
    print()


@bot.event
async def on_message(message):
    if message.content.startswith("&") and message.content.endswith("&"):
        return  # Ignore Tupperboxes being mistaken for commands.
    if not message.content.startswith(allowbrackets):
        message.content = removeBrackets(message.content)
    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    # DigiException handling
    if isinstance(error, errors.DigiException):
        logCmd = getattr(df, error.level, df.warn)
        logCmd(error)
        await ctx.send(error.user_message, delete_after=error.delete_after)
        return

    # Default command handling
    print(f"Ignoring exception in command {ctx.command}:", file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


@bot.event
async def on_disconnect():
    df.crit("SizeBot has been disconnected from Discord!")


# Here we load our extensions(cogs) listed above in [initial_extensions].
if __name__ == '__main__':
    for extension in initial_extensions:
        # try:
        bot.load_extension(extension)
    df.load("Loaded cogs.")

bot.run(authtoken)
