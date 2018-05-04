import discord
from discord.ext import commands
import re
import datetime
import sys
import os
import time
from datetime import date
from datetime import *
import math
import random
from decimal import *
from colored import fore, back, style, fg, bg, attr
from pathlib import Path
import string
import traceback
from discord.ext import commands
from math import *
import asyncio
import codecs

from globalsb import *

#Get authtoken from file.
with open("../_authtoken.txt") as f:
    authtoken = f.readlines()
authtoken = [x.strip() for x in authtoken]
authtoken = authtoken[0]

#Predefined variables.
prefix = '&'
description = '''SizeBot3 is a complete rewrite of SizeBot for the Macropolis server.
Written by DigiDuncan.
The SizeBot Team: DigiDuncan, AWK_, Tana, Benyovski, Arceus3521.'''
initial_extensions = ['cogs.change',
                      'cogs.mod',
                      'cogs.roleplay',
                      'cogs.set',
                      'cogs.stats',
                      #'cogs.statsplus',
                      'cogs.fun']

#Obviously we need this printed in the terminal.
print(bg(24) + fg(202) + style.BOLD +ascii + style.RESET)

bot = commands.Bot(command_prefix=prefix, description=description)
bot.remove_command("help")
bot.add_check(check)

@bot.event
#Output header.
async def on_ready():
    print(fore.CYAN + 'Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------' + style.RESET)
    await bot.change_presence(activity=discord.Game(name="Ratchet and Clank: Size Matters"))
    print(warn("Warn test."))
    print(crit("Crit test."))
    print(test("Test test."))

@bot.command()
async def register(ctx, nick:str, display:str, currentheight:str,
    baseheight:str, baseweight:str, units:str, species:str = None):
    #Registers a user for SizeBot.

    #Extract values and units.
    chu = getlet(currentheight)
    bhu = getlet(baseheight)
    bwu = getlet(baseweight)
    currentheight = getnum(currentheight)
    baseheight = getnum(baseheight)
    baseweight = getnum(baseweight)

    #Convert floats to decimals.
    currentheight = Decimal(currentheight)
    baseheight = Decimal(baseheight)
    baseweight = Decimal(baseweight)

    readable = "CH {0}, CHU {1}, BH {2}, BHU {3}, BW {4}, BWU {5}".format(currentheight, chu,
        baseheight, bhu, baseweight, bwu)
    print("Nickname: {0}, Display: {1}".format(nick, display))
    print(readable)

    #Already registered.
    if os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        await ctx.send("""Sorry! You already registered with SizeBot.
To unregister, use the `&unregister` command.""", delete_after=5)
        print(warn("Error UAE1 on user registration: {1}.".format(ctx.message.author)))
        return
    #Invalid size value.
    elif (currentheight <= 0 or
        baseheight <= 0 or
        baseweight <= 0):
        print(warn("Invalid size value."))
        await ctx.send("All values must be an integer greater than zero.", delete_after=3)
        return
    #Invalid display value.
    elif display.lower() not in ["y", "n"]:
        print(warn("display was {0}, must be Y or N.".format(display)))
        return
    elif units.lower() not in ["m", "u"]:
        print(warn("units was {0}, must be M or U.".format(units)))
        await ctx.send("Units must be `M` or `U`.", delete_after=3)
        return
    #Success.
    else:
        if species == None:
            species = "None"
        #Make an array of string items, one per line.
        with open(folder + '/users/' + str(ctx.message.author.id) + '.txt', "w+") as userfile:
            writethis = [str(nick) + newline, str(display) + newline, str(toSV(currentheight, chu)) +
                newline, str(toSV(baseheight, bhu)) + newline, str(toWV(baseweight, bwu)) + newline, "1.0"
                + newline, units + newline, species + newline]
            userfile.writelines(writethis)
            print(warn("Made a new user: {0}!").format(ctx.message.author))
            print(writethis)
            print(userfile.readlines())
        await ctx.send("Registered <@{0}>. {1}.".format(ctx.message.author.id, readable), delete_after=3)

@register.error
async def register_handler(ctx, error):
    # Check if required argument is missing.
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("""Not enough variables for `register`.
Use `&register [nick] [display (Y/N)] [currentheight] [baseheight] [baseweight] [M/U]`.""", delete_after=5)

@bot.command()
async def unregister(ctx, code = None):
    if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
    #User file missing.
        await ctx.send("""Sorry! You aren't registered with SizeBot.
To register, use the `&register` command.""", delete_after=5)
    elif code is None:
        regenhexcode()
        await ctx.send("""To unregister, use the `&unregister` command and the following code.
`{0}`""".format(readhexcode())
            , delete_after=5)
    elif code != readhexcode():
        await ctx.send("Incorrect code. You said: `{0}`. The correct code was: `{1}`. Try again.".format(
            code, readhexcode()), delete_after=5)
    else:
        await ctx.send("Correct code! Unregisted {0}".format(ctx.message.author.name), delete_after=3)
        os.remove(folder + "/users/" + str(ctx.message.author.id) + ".txt")

@bot.event
async def on_message(message):
    #Easter egg.
    if "monika" in message.content.lower():
        if message.author.id != sizebot_id:
            print(warn("Monika detected."))
            if random.randrange(10) == 7:
                print(warn("Monika triggered."))
                await message.channel.send(monikaline() + "<:monikajump:395732463902523393>"
                    ,delete_after=5)

    #Accurate!
    if message.content == "^":
        print(warn("Accuracy detected."))
        await message.channel.send("Yes! What that person said is accurate!")

    #Change user nick if display is Y.
    #TODO: Rewrite this, this is awful.
    if os.path.exists(folder + '/users/' + str(message.author.id) + '.txt'):
        userarray = read_user(message.author.id)
        if userarray[CHEI] == "None":
            userarray[CHEI] = userarray[BHEI]
            await message.channel.send("<@{0}>: Error in size value: Size value returned None. Resetting to base height.").format(message.author.id)
        if userarray[DISP] == "Y\n":
            if message.author.id != noboru:
                if userarray[UNIT] == "M\n":
                    if userarray[SPEC] == "None\n":
                        nick = userarray[NICK] + " [" + fromSV(userarray[CHEI]) + "]"
                        if len(nick) > 32:
                            nick = userarray[NICK][:-(len(nick) - 33)] + "… [" + fromSV(userarray[CHEI]) + "]"
                            if len(nick) > 32:
                                nick = userarray[NICK] + " [∞]"
                        await message.author.edit(nick = nick)
                    else:
                        nick = userarray[NICK] + " [" + fromSV(userarray[CHEI]) + ", " + userarray[SPEC] + "]"
                        if len(nick) > 32:
                            nick = userarray[NICK] + " [" + fromSV(userarray[CHEI]) + "]"
                            if len(nick) > 32:
                                nick = userarray[NICK][:-(len(nick) - 33)] + "… [" + fromSV(userarray[CHEI]) + "]"
                                if len(nick) > 32:
                                    nick = userarray[NICK] + " [∞]"
                        await message.author.edit(nick = nick)
                else:
                    if userarray[SPEC] == "None\n":
                        nick = userarray[NICK] + " [" + fromSVUSA(userarray[CHEI]) + "]"
                        if len(nick) > 32:
                            nick = userarray[NICK][:-(len(nick) - 33)] + "… [" + fromSVUSA(userarray[CHEI]) + "]"
                            if len(nick) > 32:
                                nick = userarray[NICK] + " [∞]"
                        await message.author.edit(nick = nick)
                    else:
                        nick = userarray[NICK] + " [" + fromSVUSA(userarray[CHEI]) + ", " + userarray[SPEC] + "]"
                        if len(nick) > 32:
                            nick = userarray[NICK] + " [" + fromSVUSA(userarray[CHEI]) + "]"
                            if len(nick) > 32:
                                nick = userarray[NICK][:-(len(nick) - 33)] + "… [" + fromSVUSA(userarray[CHEI]) + "]"
                                if len(nick) > 32:
                                    nick = userarray[NICK] + " [∞]"
                        await message.author.edit(nick = nick)

    await bot.process_commands(message)

# Here we load our extensions(cogs) listed above in [initial_extensions].
if __name__ == '__main__':
    for extension in initial_extensions:
        #try:
        bot.load_extension(extension)


bot.run(authtoken)
