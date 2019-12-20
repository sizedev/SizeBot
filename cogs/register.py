import random

from discord.ext import commands
from discord.utils import get

import digiformatter as df
from globalsb import nickUpdate
import conf
import userdb
import digiSV


async def addUserRole(member):
    role = get(member.guild.roles, id=conf.sizebotuser_roleid)
    if role is None:
        df.warn(f"Sizebot user role {conf.sizebotuser_roleid} not found in guild {member.guild.id}")
        return
    await member.add_roles(role, reason="Registered as sizebot user")


async def removeUserRole(member):
    role = get(member.guild.roles, id=conf.sizebotuser_roleid)
    if role is None:
        df.warn(f"Sizebot user role {conf.sizebotuser_roleid} not found in guild {member.guild.id}")
        return
    await member.remove_roles(role, reason="Unregistered as sizebot user")


def regenHexCode():
    # 16-char hex string gen for unregister
    hexdigits = "1234567890abcdef"
    hexcode = "".join(random.choice(hexdigits) for _ in range(16))
    with open(conf.hexfilepath, "w") as file:
        file.write(hexcode)
    return hexcode


def readHexCode():
    # Read the hexcode from the file
    with open(conf.hexfilepath, "r") as file:
        hexcode = file.readline().rstrip()
    return hexcode


class RegisterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Registers a user for SizeBot
    @commands.command()
    async def register(self, ctx, nick: str, display: str, currentheight: str, baseheight: str, baseweight: str, units: str, species: str = None):
        readable = "CH {0}, BH {1}, BW {2}".format(currentheight, baseheight, baseweight)
        df.warn("New user attempt! Nickname: {0}, Display: {1}".format(nick, display))
        print(readable)

        currentheightSV = digiSV.toWV(currentheight)
        baseheightSV = digiSV.toWV(baseheight)
        baseweightWV = digiSV.toWV(baseweight)

        # Already registered
        if userdb.exists(ctx.message.author.id):
            await ctx.send("""Sorry! You already registered with SizeBot.
    To unregister, use the `&unregister` command.""", delete_after=10)
            df.warn("User already registered on user registration: {1}.".format(ctx.message.author))
            return

        # Invalid size value
        if (currentheightSV <= 0 or baseheightSV <= 0 or baseweightWV <= 0):
            df.warn("Invalid size value.")
            await ctx.send("All values must be an integer greater than zero.", delete_after=5)
            return

        # Invalid display value
        if display.lower() not in ["y", "n"]:
            df.warn("display was {0}, must be Y or N.".format(display))
            return

        # Invalid unit value
        if units.lower() not in ["m", "u"]:
            df.warn("units was {0}, must be M or U.".format(units))
            await ctx.send("Units must be `M` or `U`.", delete_after=5)
            return

        # Success.
        if species is None:
            species = "None"

        userdata = userdb.User()
        userdata.nickname = nick
        userdata.display = display
        userdata.height = digiSV.toSV(currentheight)
        userdata.baseheight = digiSV.toSV(baseheight)
        userdata.baseweight = digiSV.toWV(baseweight)
        userdata.units = units
        userdata.species = species

        userdb.save(userdata)

        await addUserRole(ctx.message.author)

        df.warn("Made a new user: {0}!".format(ctx.message.author))
        print(userdata)
        await ctx.send("Registered <@{0}>. {1}.".format(ctx.message.author.id, readable), delete_after=5)

    @register.error
    async def register_handler(self, ctx, error):
        # Check if required argument is missing.
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("""Not enough variables for `register`.
    Use `&register [nick] [display (Y/N)] [currentheight] [baseheight] [baseweight] [M/U]`.""", delete_after=30)

    @commands.command()
    async def unregister(self, ctx, code=None):
        # User file missing
        if not userdb.exists(ctx.message.author.id):
            df.warn(f"User {ctx.message.author.id} not registered with SizeBot, but tried to unregister anyway.")
            await ctx.send("Sorry! You aren't registered with SizeBot.\n"
                           "To register, use the `&register` command.", delete_after=5)
            return

        if code is None:
            hexcode = regenHexCode()
            await ctx.send("To unregister, use the `&unregister` command and the following code.\n"
                           f"`{hexcode}`", delete_after=30)
            return

        hexcode = readHexCode()
        if code != hexcode:
            df.warn(f"User {ctx.message.author.id} tried to unregister, but said the wrong hexcode.")
            await ctx.send(f"Incorrect code. You said: `{code}`. The correct code was: `{hexcode}`. Try again.", delete_after=10)
            return

        userdb.delete(ctx.message.author.id)
        await removeUserRole(ctx.message.author)

        df.warn(f"User {ctx.message.author.id} successfully unregistered.")
        await ctx.send(f"Correct code! Unregistered {ctx.message.author.name}", delete_after=5)

    @commands.Cog.listener()
    async def on_message(self, m):
        await nickUpdate(m.author)


# Necessary.
def setup(bot):
    bot.add_cog(RegisterCog(bot))
