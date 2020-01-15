import asyncio

from discord.ext import commands
from discord.utils import get
from sizebot.discordplus import commandsplus

from sizebot import digilogger as logger
from sizebot import conf
from sizebot import userdb
from sizebot.digiSV import SV, WV
from sizebot import digisize


async def addUserRole(member):
    sizebotuserroleid = conf.getId("sizebotuserrole")
    role = get(member.guild.roles, id = sizebotuserroleid)
    if role is None:
        await logger.warn(f"Sizebot user role {sizebotuserroleid} not found in guild {member.guild.id}")
        return
    await member.add_roles(role, reason = "Registered as sizebot user")


async def removeUserRole(member):
    sizebotuserroleid = conf.getId("sizebotuserrole")
    role = get(member.guild.roles, id = sizebotuserroleid)
    if role is None:
        await logger.warn(f"Sizebot user role {sizebotuserroleid} not found in guild {member.guild.id}")
        return
    await member.remove_roles(role, reason = "Unregistered as sizebot user")


class RegisterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TODO: Change the way this works.
    @commandsplus.command()
    @commands.guild_only()
    async def register(self, ctx, nick: str, display: str = "y", currentheight: SV = userdb.defaultheight, baseheight: SV = userdb.defaultheight, baseweight: WV = userdb.defaultweight, unitsystem: str = "m", species: str = None):
        """Registers a user for SizeBot"""
        readable = f"CH {currentheight}, BH {baseheight}, BW {baseweight}"
        await logger.warn(f"New user attempt! Nickname: {nick}, Display: {display}")
        await logger.info(readable)

        # Already registered
        if userdb.exists(ctx.message.author.id):
            await ctx.send("Sorry! You already registered with SizeBot.\n"
                           "To unregister, use the `&unregister` command.")
            await logger.warn(f"User already registered on user registration: {ctx.message.author}.")
            return

        # Invalid size value
        if (currentheight <= 0 or baseheight <= 0 or baseweight <= 0):
            await logger.warn("Invalid size value.")
            await ctx.send("All values must be an integer greater than zero.")
            return

        # Invalid display value
        if display.lower() not in ["y", "n"]:
            await logger.warn(f"display was {display}, must be Y or N.")
            await ctx.send(f"display was {display}, must be Y or N.")
            return

        # Invalid unit value
        if unitsystem.lower() not in ["m", "u"]:
            await logger.warn(f"unitsystem was {unitsystem}, must be M or U.")
            await ctx.send("Unitsystem must be `M` or `U`.")
            return

        userdata = userdb.User()
        userdata.id = ctx.message.author.id
        userdata.nickname = nick
        userdata.display = display == "y"
        userdata.height = currentheight
        userdata.baseheight = baseheight
        userdata.baseweight = baseweight
        userdata.unitsystem = unitsystem
        userdata.species = species

        userdb.save(userdata)

        await addUserRole(ctx.message.author)

        await logger.warn(f"Made a new user: {ctx.message.author}!")
        await logger.info(userdata)
        await ctx.send(f"Registered <@{ctx.message.author.id}>. {readable}.")

        # user has display == "y" and is server owner
        if userdata.display and userdata.id == ctx.message.author.guild.owner.id:
            await ctx.send("I can't update a server owner's nick. You'll have to manage it manually.")
            return

    @register.error
    async def register_handler(self, ctx, error):
        # Check if required argument is missing
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "Not enough variables for `register`.\n"
                "Use `&register [nick] [display (Y/N)] [currentheight] [baseheight] [baseweight] [M/U]`.")
            return
        raise error

    @commandsplus.command()
    @commands.guild_only()
    async def unregister(self, ctx):
        user = ctx.message.author
        # User is not registered
        if not userdb.exists(user.id):
            await logger.warn(f"User {user.id} not registered with SizeBot, but tried to unregister anyway.")
            await ctx.send("Sorry! You aren't registered with SizeBot.\n"
                           "To register, use the `&register` command.")
            return

        # Send a confirmation request
        unregisterEmoji = "✔️"  # TODO: Shouldn't this be in the config?
        cancelEmoji = "❌"  # TODO: Shouldn't this be in the config?
        sentMsg = await ctx.send(f"To unregister, react with {unregisterEmoji}.")
        await sentMsg.add_reaction(unregisterEmoji)
        await sentMsg.add_reaction(cancelEmoji)

        # Wait for requesting user to react to sent message with unregisterEmoji or cancelEmoji
        def check(reaction, reacter):
            return reaction.message.id == sentMsg.id \
                and reacter.id == user.id \
                and (
                    str(reaction.emoji) == unregisterEmoji
                    or str(reaction.emoji) == cancelEmoji
                )

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            # User took too long to respond
            return
        finally:
            # User took too long OR User clicked the emoji
            await sentMsg.delete()

        # if the reaction isn't the right one, stop.
        if reaction != unregisterEmoji:
            return

        # remove the sizetag, delete the user file, and remove the user role
        await digisize.nickReset(user)
        userdb.delete(user.id)
        await removeUserRole(user)

        await logger.warn(f"User {user.id} successfully unregistered.")
        await ctx.send(f"Unregistered {user.name}.")

    @commands.Cog.listener()
    async def on_message(self, m):
        await digisize.nickUpdate(m.author)


def setup(bot):
    bot.add_cog(RegisterCog(bot))
