import asyncio

from discord.ext import commands
from discord.utils import get

from sizebot import digiformatter as df
from sizebot.conf import conf
from sizebot import userdb
from sizebot import digiSV
from sizebot import digisize


async def addUserRole(member):
    sizebotuserroleid = conf.getId("sizebotuserrole")
    role = get(member.guild.roles, id = sizebotuserroleid)
    if role is None:
        df.warn(f"Sizebot user role {sizebotuserroleid} not found in guild {member.guild.id}")
        return
    await member.add_roles(role, reason = "Registered as sizebot user")


async def removeUserRole(member):
    sizebotuserroleid = conf.getId("sizebotuserrole")
    role = get(member.guild.roles, id = sizebotuserroleid)
    if role is None:
        df.warn(f"Sizebot user role {sizebotuserroleid} not found in guild {member.guild.id}")
        return
    await member.remove_roles(role, reason = "Unregistered as sizebot user")


class RegisterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Registers a user for SizeBot
    @commands.command()
    async def register(self, ctx, nick: str, display: str = "y", currentheight: str = "5ft10in", baseheight: str = "5ft10in", baseweight: str = "180lb", unitsystem: str = "m", species: str = None):
        readable = "CH {0}, BH {1}, BW {2}".format(currentheight, baseheight, baseweight)
        df.warn("New user attempt! Nickname: {0}, Display: {1}".format(nick, display))
        print(readable)

        currentheightSV = digiSV.toSV(currentheight)
        baseheightSV = digiSV.toSV(baseheight)
        baseweightWV = digiSV.toWV(baseweight)

        # Already registered
        if userdb.exists(ctx.message.author.id):
            await ctx.send("Sorry! You already registered with SizeBot.\n"
                           "To unregister, use the `&unregister` command.", delete_after = 10)
            df.warn("User already registered on user registration: {1}.".format(ctx.message.author))
            return

        # Invalid size value
        if (currentheightSV <= 0 or baseheightSV <= 0 or baseweightWV <= 0):
            df.warn("Invalid size value.")
            await ctx.send("All values must be an integer greater than zero.", delete_after = 5)
            return

        # Invalid display value
        if display.lower() not in ["y", "n"]:
            df.warn("display was {0}, must be Y or N.".format(display))
            return

        # Invalid unit value
        if unitsystem.lower() not in ["m", "u"]:
            df.warn("unitsystem was {0}, must be M or U.".format(unitsystem))
            await ctx.send("Unitsystem must be `M` or `U`.", delete_after = 5)
            return

        userdata = userdb.User()
        userdata.id = ctx.message.author.id
        userdata.nickname = nick
        userdata.display = display
        userdata.height = currentheightSV
        userdata.baseheight = baseheightSV
        userdata.baseweight = baseweightWV
        userdata.unitsystem = unitsystem
        userdata.species = species

        userdb.save(userdata)

        await addUserRole(ctx.message.author)

        df.warn(f"Made a new user: {ctx.message.author}!")
        print(userdata)
        await ctx.send(f"Registered <@{ctx.message.author.id}>. {readable}.", delete_after = 5)

    @register.error
    async def register_handler(self, ctx, error):
        # Check if required argument is missing
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Not enough variables for `register`.\n"
                           "Use `&register [nick] [display (Y/N)] [currentheight] [baseheight] [baseweight] [M/U]`.",
                           delete_after = 30)
            return
        raise error

    @commands.command()
    async def unregister(self, ctx):
        # User file missing
        if not userdb.exists(ctx.message.author.id):
            df.warn(f"User {ctx.message.author.id} not registered with SizeBot, but tried to unregister anyway.")
            await ctx.send("Sorry! You aren't registered with SizeBot.\n"
                           "To register, use the `&register` command.", delete_after = 5)
            return

        unregisterIcon = "❌"
        sentMsg = await ctx.send(f"To unregister, react with {unregisterIcon}")
        await sentMsg.add_reaction(unregisterIcon)

        def check(reaction, user):
            print(reaction)
            print(user)
            return reaction.message.id == sentMsg.id \
                and user.id == ctx.message.author.id \
                and str(reaction.emoji) == unregisterIcon

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            return
        finally:
            await sentMsg.delete()

        userdb.delete(ctx.message.author.id)
        await removeUserRole(ctx.message.author)

        df.warn(f"User {ctx.message.author.id} successfully unregistered.")
        await ctx.send(f"Unregistered {ctx.message.author.name}", delete_after = 5)

    @commands.Cog.listener()
    async def on_message(self, m):
        await digisize.nickUpdate(m.author)


# Necessary
def setup(bot):
    bot.add_cog(RegisterCog(bot))
