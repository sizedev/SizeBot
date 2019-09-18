from globalsb import *
from globalsb import yukioid, digiid
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
initial_extensions = [
    'cogs.change',
    'cogs.mod',
    'cogs.roleplay',
    'cogs.set',
    'cogs.stats',
    'cogs.fun',
    'cogs.dm',
    'cogs.register'
]

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
    if ((message.author.id == yukioid and ";)" in message.content.replace(" ", ""))
        or (message.author.id == yukioid and ":wink:" in message.content.replace(" ", ""))
        or (message.author.id == yukioid and "😉" in message.content.replace(" ", ""))):
        with open("../winkcount.txt", "r") as winkfile:
            try:
                winkcount = int(winkfile.read())
            except ValueError:
                winkcount = 0
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
