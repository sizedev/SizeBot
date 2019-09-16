from globalsb import *
from globalsb import yukioid, warn
import digilogger as logger

launch = datetime.now()

os.system("")

# Get authtoken from file.
with open("../_authtoken.txt") as f:
    authtoken = f.readlines()
authtoken = [x.strip() for x in authtoken]
authtoken = authtoken[0]

# Predefined variables.
prefix = '&'
description = '''SizeBot3 is a complete rewrite of SizeBot for the Macropolis server.
Written by DigiDuncan.
The SizeBot Team: DigiDuncan, AWK_, Benyovski, Arceus3521, Surge The Raichu.'''
initial_extensions = ['cogs.change',
                      'cogs.mod',
                      'cogs.roleplay',
                      'cogs.set',
                      'cogs.stats',
                      'cogs.fun']

# Obviously we need this printed in the terminal.
print(bg(24) + fg(202) + style.BOLD + ascii + style.RESET)

bot = commands.Bot(command_prefix=prefix, description=description)
bot.remove_command("help")
bot.add_check(check)


@bot.event
# Output header.
async def on_ready():
    print(fore.CYAN + 'Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------' + style.RESET)
    await bot.change_presence(activity=discord.Game(name="Ratchet and Clank: Size Matters"))
    logger.warn("Warn test.")
    logger.crit("Crit test.")
    logger.test("Test test.")
    finishlaunch = datetime.now()
    elapsed = finishlaunch - launch
    logger.test(f"SizeBot launched in {round((elapsed.total_seconds() * 1000), 3)} milliseconds.")
    print()


@bot.command()
async def register(ctx, nick: str, display: str, currentheight: str,
                   baseheight: str, baseweight: str, units: str, species: str = None):
    # Registers a user for SizeBot.

    # Fix feet and inches.
    currentheight = isFeetAndInchesAndIfSoFixIt(currentheight)
    baseheight = isFeetAndInchesAndIfSoFixIt(baseheight)

    # Extract values and units.
    chu = getlet(currentheight)
    bhu = getlet(baseheight)
    bwu = getlet(baseweight)
    currentheight = getnum(currentheight)
    baseheight = getnum(baseheight)
    baseweight = getnum(baseweight)

    # Convert floats to decimals.
    currentheight = Decimal(currentheight)
    baseheight = Decimal(baseheight)
    baseweight = Decimal(baseweight)

    readable = "CH {0}, CHU {1}, BH {2}, BHU {3}, BW {4}, BWU {5}".format(currentheight, chu,
                                                                          baseheight, bhu, baseweight, bwu)
    logger.warn("New user attempt! Nickname: {0}, Display: {1}".format(nick, display))
    print(readable)

    # Already registered.
    if os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        await ctx.send("""Sorry! You already registered with SizeBot.
To unregister, use the `&unregister` command.""", delete_after=5)
        logger.warn("User already registered on user registration: {1}.".format(ctx.message.author))
        return
    # Invalid size value.
    elif (currentheight <= 0 or
            baseheight <= 0 or
            baseweight <= 0):
        logger.warn("Invalid size value.")
        await ctx.send("All values must be an integer greater than zero.", delete_after=3)
        return
    # Invalid display value.
    elif display.lower() not in ["y", "n"]:
        logger.warn("display was {0}, must be Y or N.".format(display))
        return
    elif units.lower() not in ["m", "u"]:
        logger.warn("units was {0}, must be M or U.".format(units))
        await ctx.send("Units must be `M` or `U`.", delete_after=3)
        return
    # Success.
    else:
        if species is None:
            species = "None"
        # Make an array of string items, one per line.
        with open(folder + '/users/' + str(ctx.message.author.id) + '.txt', "w+") as userfile:
            writethis = [str(nick) + newline, str(display) + newline, str(toSV(currentheight, chu)) +
                         newline, str(toSV(baseheight, bhu)) + newline, str(toWV(baseweight, bwu)) + newline, "1.0"
                         + newline, units + newline, species + newline]
            try:
                userfile.writelines(writethis)
            except UnicodeDecodeError():
                warn("Unicode in nick or species.")
                await ctx.send("<@{0}> Unicode error! Please don't put Unicode characters in your nick or species.".format(ctx.message.author.id))
                return
            logger.warn("Made a new user: {0}!".format(ctx.message.author))
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
async def unregister(ctx, code=None):
    if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
        # User file missing.
        logger.warn("User {0} not registered with SizeBot, but tried to unregister anyway.".format(ctx.message.author.id))
        await ctx.send("""Sorry! You aren't registered with SizeBot.
To register, use the `&register` command.""", delete_after=5)
    elif code is None:
        regenhexcode()
        await ctx.send("""To unregister, use the `&unregister` command and the following code.
`{0}`""".format(readhexcode()), delete_after=5)
    elif code != readhexcode():
        logger.warn("User {0} tried to unregister, but said the wrong hexcode.".format(ctx.message.author.id))
        await ctx.send("Incorrect code. You said: `{0}`. The correct code was: `{1}`. Try again.".format(
            code, readhexcode()), delete_after=5)
    else:
        logger.warn("User {0} successfully unregistered.".format(ctx.message.author.id))
        await ctx.send("Correct code! Unregisted {0}".format(ctx.message.author.name), delete_after=3)
        os.remove(folder + "/users/" + str(ctx.message.author.id) + ".txt")


@bot.event
async def on_message(message):
    # Easter egg.
    if "monika" in message.content.lower():
        if message.author.id != sizebot_id:
            logger.warn("Monika detected.")
            if random.randrange(6) == 1:
                logger.warn("Monika triggered.")
                await message.channel.send(monikaline(), delete_after=7)

    # Yukio wink count.
    if message.author.id == yukioid and ";)" in message.content.replace(" ", ""):
        with open("../winkcount.txt", "r") as winkfile:
            winkcount = int(winkfile.read())
        winkcount += 1
        with open("../winkcount.txt", "w") as winkfile:
            winkfile.write(str(winkcount))
        logger.msg(f"Yukio has winked {winkcount} times!")

    try:
        await nickupdate(message.author)
    except discord.ext.commands.errors.CommandInvokeError:
        pass

    await bot.process_commands(message)

# Here we load our extensions(cogs) listed above in [initial_extensions].
if __name__ == '__main__':
    for extension in initial_extensions:
        # try:
        bot.load_extension(extension)


bot.run(authtoken)
