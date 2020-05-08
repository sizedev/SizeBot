import asyncio
import logging
from shutil import copyfile

from discord.utils import get
from sizebot.discordplus import commands

from sizebot import conf
from sizebot.lib import errors, proportions, userdb
from sizebot.lib.constants import ids, emojis
from sizebot.lib.units import SV, WV

logger = logging.getLogger("sizebot")


async def addUserRole(member):
    role = get(member.guild.roles, id=ids.sizebotuserrole)
    if role is None:
        logger.warn(f"Sizebot user role {ids.sizebotuserrole} not found in guild {member.guild.id}")
        return
    await member.add_roles(role, reason="Registered as sizebot user")


async def removeUserRole(member):
    role = get(member.guild.roles, id=ids.sizebotuserrole)
    if role is None:
        logger.warn(f"Sizebot user role {ids.sizebotuserrole} not found in guild {member.guild.id}")
        return
    await member.remove_roles(role, reason="Unregistered as sizebot user")


class RegisterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TODO: Change the way this works.
    @commands.command(
        aliases = ["signup"],
        usage = "<nick> <display: Y/N> <currentheight> <baseheight> <baseweight> <system: M/U> [species]",
        category = "setup"
    )
    @commands.guild_only()
    async def register(self, ctx, nick: str, display: str = "y", currentheight: SV = userdb.defaultheight, baseheight: SV = userdb.defaultheight, baseweight: WV = userdb.defaultweight, unitsystem: str = "m", species: str = None):
        """Registers a user for SizeBot.

        Parameters:
        • `nick`: Your nickname. This will be the first thing displayed in your nickname.
        For a nickname with spaces, this must be wrapped in quotes.
        • `display`: Whether or not to have SizeBot manage your server nickname for you,
        allowing for an automatically updated sizetag appended to your nickname at all times.
        • `currentheight`: Self-explnatory. Accepts a wide variety of units as shown in `&units`.
        • `baseheight`: The default height of your character. It is recommended that this is a vaugely
        reasonable, human-like value, for instance your IRL height, except in rare circumnstances
        (for instance, if your character is a cat, or an orc, etc.)
        • `baseweight`: The default weight of your character. All the recommendations for baseheight apply here.
        • `unitsystem`: The unit system your size tag, and basic versions of your stats, will be displayed in by default.
        Accepts `M` for Metric, and `U` or `I` for U.S./Imperial.
        • `species`: Optional, a string to be appened after your size in your sizetag. Appears in the format `<nick> [<size>, <species>]`.
        If `species` is to contain a space, wrap it in quotes.

        Examples:
        `&register DigiDuncan Y 0.5in 5'7.5 120lb U`
        `&register Surge Y 11ft 5'8 140lb U Raichu`
        `&register "Speck Boi" Y 0.1mm 190cm 120kg M`
        """
        readable = f"CH {currentheight}, BH {baseheight}, BW {baseweight}"
        logger.warn(f"New user attempt! Nickname: {nick}, Display: {display}")
        logger.info(readable)

        # Already registered
        if userdb.exists(ctx.guild.id, ctx.author.id):
            await ctx.send("Sorry! You already registered with SizeBot.\n"
                           "To unregister, use the `&unregister` command.")
            logger.warn(f"User already registered on user registration: {ctx.author}.")
            return

        currentusers = userdb.listUsers()
        guildsregisteredin = [self.bot.get_guild(int(g)).name for g, u in currentusers if u == ctx.author.id]
        if guildsregisteredin != []:
            guildsstring = guildsregisteredin.join('\n')
            sentMsg = await ctx.send(f"You are already registed with SizeBot in these servers:\n{guildsstring}"
                                     f"You can copy a profile from one of these guilds to this one using `{conf.prefix}copy.`\n"
                                     "Proceed with registration anyway?")
            await sentMsg.add_reaction(emojis.check)
            await sentMsg.add_reaction(emojis.cancel)

            # Wait for requesting user to react to sent message with emojis.check or emojis.cancel
            def check(reaction, reacter):
                return reaction.message.id == sentMsg.id \
                    and reacter.id == ctx.author.id \
                    and (
                        str(reaction.emoji) == emojis.check
                        or str(reaction.emoji) == emojis.cancel
                    )

            try:
                reaction, ctx.author = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                # User took too long to respond
                await sentMsg.delete()

            # if the reaction isn't the right one, stop.
            if reaction.emoji != emojis.check:
                return

        # Invalid size value
        if (currentheight <= 0 or baseheight <= 0 or baseweight <= 0):
            logger.warn("Invalid size value.")
            await ctx.send("All values must be an integer greater than zero.")
            return

        # Invalid display value
        if display.lower() not in ["y", "n"]:
            logger.warn(f"display was {display}, must be Y or N.")
            await ctx.send(f"display was {display}, must be Y or N.")
            return

        # Invalid unit value
        if unitsystem.lower() not in ["m", "u", "i"]:
            logger.warn(f"unitsystem was {unitsystem}, must be M or U/I.")
            await ctx.send("Unitsystem must be `M` or `U`/`I`.")
            raise errors.InvalidUnitSystemException

        # I system is really U.
        if unitsystem.lower() == "i":
            unitsystem = "u"

        userdata = userdb.User()
        userdata.guildid = ctx.guild.id
        userdata.id = ctx.author.id
        userdata.nickname = nick
        userdata.display = display.lower() == "y"
        userdata.height = currentheight
        userdata.baseheight = baseheight
        userdata.baseweight = baseweight
        userdata.unitsystem = unitsystem
        userdata.species = species

        userdb.save(userdata)

        await addUserRole(ctx.author)

        logger.warn(f"Made a new user: {ctx.author}!")
        logger.info(userdata)
        await ctx.send(f"Registered <@{ctx.author.id}>. {readable}.")

        # user has display == "y" and is server owner
        if userdata.display and userdata.id == ctx.author.guild.owner.id:
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

    @commands.command(
        category = "setup"
    )
    @commands.guild_only()
    async def unregister(self, ctx):
        """Unregister your SizeBot profile."""
        guild = ctx.guild
        user = ctx.author
        # User is not registered
        if not userdb.exists(guild.id, user.id):
            logger.warn(f"User {user.id} not registered with SizeBot, but tried to unregister anyway.")
            await ctx.send("Sorry! You aren't registered with SizeBot.\n"
                           "To register, use the `&register` command.")
            return

        # Send a confirmation request
        # TODO: Replace this with a Menu.
        sentMsg = await ctx.send(f"To unregister, react with {emojis.check}.")
        await sentMsg.add_reaction(emojis.check)
        await sentMsg.add_reaction(emojis.cancel)

        # Wait for requesting user to react to sent message with emojis.check or emojis.cancel
        def check(reaction, reacter):
            return reaction.message.id == sentMsg.id \
                and reacter.id == user.id \
                and (
                    str(reaction.emoji) == emojis.check
                    or str(reaction.emoji) == emojis.cancel
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
        if reaction.emoji != emojis.check:
            return

        # remove the sizetag, delete the user file, and remove the user role
        await proportions.nickReset(user)
        userdb.delete(guild.id, user.id)
        await removeUserRole(user)

        logger.warn(f"User {user.id} successfully unregistered.")
        await ctx.send(f"Unregistered {user.name}.")

    @commands.command(
        category = "setup"
    )
    @commands.guild_only()
    async def copy(self, ctx):
        """Copy your SizeBot profile from a different guild to this one."""

        inputdict = {
            "1️⃣": 1,
            "2️⃣": 2,
            "3️⃣": 3,
            "4️⃣": 4,
            "5️⃣": 5,
            "6️⃣": 6,
            "7️⃣": 7,
            "8️⃣": 8,
            "9️⃣": 9,
            "0️⃣": 10
        }

        currentusers = userdb.listUsers()
        guildsregisteredin = [g for g, u in currentusers if u == ctx.author.id]
        guildsregisteredinnames = [self.bot.get_guild(g).name for g, u in currentusers if u == ctx.author.id]

        if guildsregisteredin == []:
            await ctx.send("You are not registered with SizeBot in any guilds."
                           f"To register, use `{conf.prefix}register`.")
            return

        # TODO: This doesn't seem to work.
        if guildsregisteredin == [ctx.guild.id]:
            await ctx.send("You are not registered with SizeBot in any other guilds.")
            return

        outmsg = await ctx.send(emojis.loading)
        outstring = ""

        if userdb.exists(ctx.guild.id, ctx.author.id):
            outstring += "**:rotating_light:WARNING::rotating_light:**\n**You are already registered with SizeBot on this guild. Copying a profile to this guild will overwrite any size data you have here. Proceed with caution.**\n\n"

        outstring += "Copy profile from what guild?\n"

        # TODO: Replace this with a Menu.
        for i in range(min(len(guildsregisteredin), 10)):  # Loops over either the whole list of guilds, or if that's longer than 10, 10 times.
            outstring += f"{list(inputdict.keys())[i]} *{guildsregisteredinnames[i]}*\n"
            await outmsg.add_reaction(list(inputdict.keys())[i])
        await outmsg.add_reaction(emojis.cancel)

        outstring += f"\nClick {emojis.cancel} to cancel."

        await outmsg.edit(content = outstring)

        # Wait for requesting user to react to sent message with emojis.check or emojis.cancel
        def check(reaction, reacter):
            return reaction.message.id == outmsg.id \
                and reacter.id == ctx.author.id \
                and (
                    str(reaction.emoji) == emojis.check
                    or str(reaction.emoji) in inputdict.keys()
                )

        try:
            reaction, ctx.author = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            # User took too long to respond
            await outmsg.delete()
            return

        # if the reaction isn't the right one, stop.
        if reaction.emoji == emojis.cancel:
            await outmsg.delete()
            return

        if reaction.emoji in inputdict.keys():
            chosen = inputdict[reaction.emoji] - 1
            chosenguild = guildsregisteredin[chosen]

            frompath = conf.guilddbpath / str(chosenguild) / "users" / f"{ctx.author.id}.json"
            topath = conf.guilddbpath / str(ctx.guild.id) / "users" / f"{ctx.author.id}.json"

            topath.parent.mkdir(parents = True, exist_ok = True)

            copyfile(frompath, topath)

            await outmsg.delete()
            await ctx.send(f"Successfully copied profile from *{self.bot.get_guild(int(chosenguild)).name}* to here!")

        else:
            await outmsg.delete()
            raise errors.ThisShouldNeverHappenException


def setup(bot):
    bot.add_cog(RegisterCog(bot))
