import asyncio
import logging

from discord.utils import get
from discord.ext import commands

from sizebot.conf import conf
from sizebot.lib import errors, telemetry, userdb, nickmanager
from sizebot.lib.constants import ids, emojis
from sizebot.lib.units import SV, WV

logger = logging.getLogger("sizebot")


async def add_user_role(member):
    role = get(member.guild.roles, id=ids.sizebotuserrole)
    if role is None:
        # logger.warn(f"Sizebot user role {ids.sizebotuserrole} not found in guild {member.guild.id}")
        return
    # PERMISSION: requires manage_roles
    await member.add_roles(role, reason="Registered as SizeBot user")


async def remove_user_role(member):
    role = get(member.guild.roles, id=ids.sizebotuserrole)
    if role is None:
        # logger.warn(f"Sizebot user role {ids.sizebotuserrole} not found in guild {member.guild.id}")
        return
    # PERMISSION: requires manage_roles
    await member.remove_roles(role, reason="Unregistered as SizeBot user")


async def show_next_step(ctx, userdata: userdb.User, completed=False):
    if completed or not userdata.registered:
        telemetry.RegisterStepCompleted(ctx.guild.id, ctx.author.id, ctx.command.name, completed = completed).save()

    if completed:
        congrats_message = (
            f"Congratulations, {ctx.author.display_name}, you're all set up with SizeBot! Here are some next steps you might want to take:\n"
            f"* You can use `{conf.prefix}setspecies` to set your species to be shown in your sizetag.\n"
            f"* You can adjust your current height with `{conf.prefix}setheight`."
        )
        if ctx.me.guild_permissions.manage_nicknames:
            congrats_message += f"\n* You can turn off sizetags with `{conf.prefix}setdisplay N`."
        await ctx.send(congrats_message)

    if userdata.registered:
        return
    next_step = userdata.registration_steps_remaining[0]
    step_messages = {
        "setheight": f"To start, set your current height with {conf.prefix}setheight. You can always change this later.\n*Examples: `{conf.prefix}setheight 200ft` or `{conf.prefix}setheight 0.5in`*",
        "setbaseheight": f"Next, set your base height with `{conf.prefix}setbaseheight`. This should be roughly a human height in order for comparisons to make better sense.\n*Examples: `{conf.prefix}setbaseheight 5ft6in` or `{conf.prefix}setbaseheight 170cm`*",
        "setbaseweight": f"Now, use `{conf.prefix}setbaseweight` to set your base weight. This should be whatever weight you'd be at your base height.\n*Examples: `{conf.prefix}setbaseweight 120lb` or `{conf.prefix}setbaseweight 80kg`*",
        "setsystem": f"Finally, use `{conf.prefix}setsystem` to set what unit system you use: `M` for Metric, `U` for US.\n*Examples: `{conf.prefix}setsystem U` or `{conf.prefix}setsystem M`*"
    }
    next_step_message = step_messages[next_step]
    await ctx.send(f"You have {len(userdata.registration_steps_remaining)} registration steps remaining.\n{next_step_message}")


class RegisterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases = ["signup"],
        category = "setup"
    )
    @commands.guild_only()
    async def register(self, ctx):
        # nick: str
        # currentheight: SV = proportions.defaultheight
        # baseheight: SV = proportions.defaultheight
        # baseweight: WV = userdb.defaultweight
        # unitsystem: str = "m"
        # species: str = None
        """Registers a user for SizeBot."""

        userdata = None
        try:
            userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        except errors.UserNotFoundException:
            userdata = None

        # User data already exists
        if userdata:
            if userdata.registered:
                await ctx.send("Sorry! You already registered with SizeBot.\n"
                               f"To unregister, use the `{conf.prefix}unregister` command.")
            else:
                await show_next_step(ctx, userdata)
            return

        # User is already in different guilds, offer to copy profile to this guild?
        guilds = [self.bot.get_guild(g) for g, _ in userdb.list_users(userid=ctx.author.id)]
        guilds = [g for g in guilds if g is not None]
        guilds_names = [g.name for g in guilds]
        if guilds_names:
            guildsstring = "\n".join(guilds_names)
            sentMsg = await ctx.send(f"You are already registered with SizeBot in these servers:\n{guildsstring}\n"
                                     f"You can copy a profile from one of these guilds to this one using `{ctx.prefix}copy.`\n"
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
                return

            # if the reaction isn't the right one, stop.
            if reaction.emoji != emojis.check:
                return

        telemetry.RegisterStarted(ctx.guild.id, ctx.author.id).save()
        userdata = userdb.User()
        userdata.guildid = ctx.guild.id
        userdata.id = ctx.author.id
        userdata.nickname = ctx.author.display_name
        userdata.display = False
        if ctx.me.guild_permissions.manage_nicknames:
            userdata.display = True
            if any(c in ctx.author.display_name for c in "()[]"):
                await ctx.send(f"**If you have already have a size tag in your name, you can fix your nick with `{conf.prefix}setnick`.**")
        userdata.registration_steps_remaining = ["setheight", "setbaseheight", "setbaseweight", "setsystem"]

        # TODO: If the bot has MANAGE_NICKNAMES permission but can't change this user's permission, let the user know
        # TODO: If the bot has MANAGE_NICKNAMES permission but can't change this user's permission, and the user is an admin, let them know they may need to fix permissions

        userdb.save(userdata)

        await add_user_role(ctx.author)

        logger.warn(f"Started registration for a new user: {ctx.author} in guild {ctx.guild.name}!")
        logger.info(userdata)

        # user has display == "y" and is server owner
        if userdata.display and userdata.id == ctx.author.guild.owner.id:
            await ctx.send("I can't update a server owner's nick. You'll have to manage it manually.")

        await ctx.send("Initial registration completed!")
        await show_next_step(ctx, userdata)

    @register.error
    async def register_handler(self, ctx, error):
        # Check if required argument is missing
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "Not enough variables for `register`.\n"
                f"See `{conf.prefix}help register`.")
            return
        raise error

    @commands.command(
        aliases = ["advancedsignup", "advregister", "advsignup", "oldregister"],
        usage = "<nick> <currentheight> <baseheight> <baseweight> <system: M/U> [species]",
        category = "setup"
    )
    @commands.guild_only()
    async def advancedregister(self, ctx, nick: str, currentheight: SV = userdb.DEFAULT_HEIGHT, baseheight: SV = userdb.DEFAULT_HEIGHT, baseweight: WV = userdb.DEFAULT_WEIGHT, unitsystem: str = "m", species: str = None):
        """Registers a user for SizeBot, legacy style.

        Parameters:
        • `nick`: Your nickname. This will be the first thing displayed in your nickname. For a nickname with spaces, this must be wrapped in quotes.
        • `currentheight`: Self-explnatory.
        • `baseheight`: The default height of your character. It is recommended that this is a vaugely reasonable, human-like value, for instance your IRL height, except in rare circumnstances (for instance, if your character is a cat, or an orc, etc.)
        • `baseweight`: The default weight of your character. All the recommendations for baseheight apply here.
        • `unitsystem`: The unit system your size tag, and basic versions of your stats, will be displayed in by default. Accepts `M` for Metric, and `U` or `I` for U.S./Imperial.
        • `species`: Optional, a string to be appened after your size in your sizetag. Appears in the format `<nick> [<size>, <species>]`. If `species` is to contain a space, wrap it in quotes.

        Measurement parameters can accept a wide variety of units, as listed in `&units`.

        This command is deprecated. It may not be up to date, might break, and is definitely clunky to use. Just don't.

        Examples:
        `&advancedregister DigiDuncan 0.5in 5'7 120lb U`
        `&advancedregister Surge 11ft 5'8 140lb U Raichu`
        `&advancedregister "Speck Boi" 0.1mm 190cm 120kg M`
        """
        readable = f"CH {currentheight}, BH {baseheight}, BW {baseweight}"
        logger.warn(f"New user attempt! Nickname: {nick}")
        logger.warn("OH GOD THEY'RE USING THE OLD REGISTER COMMAND")
        logger.info(readable)

        # Already registered
        if userdb.exists(ctx.guild.id, ctx.author.id):
            await ctx.send("Sorry! You already registered with SizeBot.\n"
                           "To unregister, use the `&unregister` command.")
            logger.warn(f"User already registered on user registration: {ctx.author}.")
            return

        guilds = [self.bot.get_guild(g) for g, _ in userdb.list_users(userid=ctx.author.id)]
        guilds = [g for g in guilds if g is not None]
        guilds_names = [g.name for g in guilds]
        if guilds_names != []:
            guildsstring = "\n".join(guilds_names)
            sentMsg = await ctx.send(f"You are already registered with SizeBot in these servers:\n{guildsstring}\n"
                                     f"You can copy a profile from one of these guilds to this one using `{ctx.prefix}copy.`\n"
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

            reaction = None
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

        # Invalid unit value
        if unitsystem.lower() not in ["m", "u", "i"]:
            logger.warn(f"unitsystem was {unitsystem}, must be M or U/I.")
            await ctx.send("Unitsystem must be `M` or `U`/`I`.")
            raise errors.InvalidUnitSystemException

        # I system is really U.
        if unitsystem.lower() == "i":
            unitsystem = "u"

        telemetry.AdvancedRegisterUsed(ctx.guild.id, ctx.author.id).save()
        userdata = userdb.User()
        userdata.guildid = ctx.guild.id
        userdata.id = ctx.author.id
        userdata.nickname = nick
        userdata.display = True
        userdata.height = currentheight
        userdata.baseheight = baseheight
        userdata.baseweight = baseweight
        userdata.unitsystem = unitsystem
        userdata.species = species

        userdb.save(userdata)

        await add_user_role(ctx.author)

        logger.warn(f"Made a new user: {ctx.author}!")
        logger.info(userdata)
        await ctx.send(f"Registered <@{ctx.author.id}> in guild {ctx.guild.name}. {userdata}.")

        # user has display == "y" and is server owner
        if userdata.display and userdata.id == ctx.author.guild.owner.id:
            await ctx.send("I can't update a server owner's nick. You'll have to manage it manually.")
            return

    @advancedregister.error
    async def advancedregister_handler(self, ctx, error):
        # Check if required argument is missing
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "Not enough variables for `advancedregister`.\n"
                f"See `{conf.prefix}help advancedregister`.")
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
        if not userdb.exists(guild.id, user.id, allow_unreg=True):
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

        # remove the sizetag
        if ctx.me.guild_permissions.manage_nicknames:
            await nickmanager.nick_reset(user)
        # delete the user file
        userdb.delete(guild.id, user.id)
        # remove the user role
        await remove_user_role(user)

        telemetry.Unregistered(ctx.guild.id, ctx.author.id).save()
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

        guilds = [self.bot.get_guild(g) for g, _ in userdb.list_users(userid=ctx.author.id)]
        guilds = [g for g in guilds if g is not None]
        guilds_ids = [g.id for g in guilds]
        guilds_names = [g.name for g in guilds]

        if guilds_ids == []:
            await ctx.send("You are not registered with SizeBot in any guilds."
                           f"To register, use `{ctx.prefix}register`.")
            return

        # TODO: This doesn't seem to work.
        if guilds_ids == [ctx.guild.id]:
            await ctx.send("You are not registered with SizeBot in any other guilds.")
            return

        outmsg = await ctx.send(emojis.loading)
        outstring = ""

        if userdb.exists(ctx.guild.id, ctx.author.id):
            outstring += "**:rotating_light:WARNING::rotating_light:**\n**You are already registered with SizeBot on this guild. Copying a profile to this guild will overwrite any size data you have here. Proceed with caution.**\n\n"

        outstring += "Copy profile from what guild?\n"

        # TODO: Replace this with a Menu.
        for i in range(min(len(guilds_ids), 10)):  # Loops over either the whole list of guilds, or if that's longer than 10, 10 times.
            outstring += f"{list(inputdict.keys())[i]} *{guilds_names[i]}*\n"
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

        if reaction.emoji not in inputdict.keys():
            await outmsg.delete()
            raise errors.ThisShouldNeverHappenException

        chosen = inputdict[reaction.emoji] - 1
        chosenguildid = guilds_ids[chosen]
        userdata = userdb.load(chosenguildid, ctx.author.id)
        userdata.guildid = ctx.guild.id
        userdb.save(userdata)

        telemetry.ProfileCopied(ctx.guild.id, ctx.author.id).save()

        await outmsg.delete()
        await ctx.send(f"Successfully copied profile from *{self.bot.get_guild(int(chosenguildid)).name}* to here!")


async def setup(bot):
    await bot.add_cog(RegisterCog(bot))
