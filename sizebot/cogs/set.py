import logging
from typing import Annotated, Literal

import discord
from discord.ext import commands

from sizebot.cogs.register import show_next_step
from sizebot.lib import userdb, nickmanager
from sizebot.lib.diff import LinearRate
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.gender import Gender, parse_gender
from sizebot.lib.loglevels import EGG
from sizebot.lib.shoesize import to_shoe_size, from_shoe_size
from sizebot.lib.stats import HOUR
from sizebot.lib.types import BotContext
from sizebot.lib.units import SV, WV, pos_SV, pos_WV
from sizebot.lib.unitsystem import UnitSystem, parse_unitsystem
from sizebot.lib.utils import parse_scale, randrange_log

logger = logging.getLogger("sizebot")


class SetCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        aliases = ["changenick", "nick", "name", "changename", "setname"],
        usage = "<nick>",
        category = "set"
    )
    @commands.guild_only()
    async def setnick(self, ctx: BotContext, *, newnick: str):
        """Change nickname."""
        # TODO: Disable and hide this command on servers where bot does not have MANAGE_NICKNAMES permission
        # TODO: If the bot has MANAGE_NICKNAMES permission but can't change this user's permission, let the user know
        # TODO: If the bot has MANAGE_NICKNAMES permission but can't change this user's permission, and the user is an admin, let them know they may need to fix permissions
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.nickname = newnick
        userdb.save(userdata)

        await ctx.send(f"<@{ctx.author.id}>'s nick is now {userdata.nickname}.")

        await nickmanager.nick_update(ctx.author)
        await show_next_step(ctx, userdata)

    @commands.command(
        usage = "<species>",
        category = "set"
    )
    @commands.guild_only()
    async def setspecies(self, ctx: BotContext, *, newspecies: str):
        """Change species."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.species = newspecies
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s species is now a {userdata.species}.")

        await nickmanager.nick_update(ctx.author)
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["clearspecies"],
        category = "set"
    )
    @commands.guild_only()
    async def resetspecies(self, ctx: BotContext):
        """Remove species."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.species = None
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s species is now cleared.")

        await nickmanager.nick_update(ctx.author)
        await show_next_step(ctx, userdata)

    @commands.command(
        usage = "<Y/N>",
        category = "set"
    )
    @commands.guild_only()
    async def setdisplay(self, ctx: BotContext, newdisp: bool):
        """Set display mode."""
        # TODO: Disable and hide this command on servers where bot does not have MANAGE_NICKNAMES permission
        # TODO: If the bot has MANAGE_NICKNAMES permission but can't change this user's permission, let the user know
        # TODO: If the bot has MANAGE_NICKNAMES permission but can't change this user's permission, and the user is an admin, let them know they may need to fix permissions
        if newdisp not in [True, False]:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} [Y/N/true/false/yes/no/enable/disable...]`.")
            return

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.display = newdisp
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s display is now set to {userdata.display}.")

        await nickmanager.nick_update(ctx.author)
        await show_next_step(ctx, userdata)

    @commands.command(
        usage = "<M/U>",
        category = "set"
    )
    @commands.guild_only()
    async def setsystem(self, ctx: BotContext, newsys: Annotated[UnitSystem, parse_unitsystem]):
        """Set measurement system. (M or U.)"""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.unitsystem = newsys
        completed_registration = userdata.complete_step("setsystem")
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s system is now set to {newsys}.")

        await nickmanager.nick_update(ctx.author)
        await show_next_step(ctx, userdata, completed=completed_registration)

    @commands.command(
        aliases = ["setsize", "s"],
        usage = "<height>",
        category = "set"
    )
    @commands.guild_only()
    async def setheight(self, ctx: BotContext, *, newheight: SV):
        """Change height."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.height = newheight
        completed_registration = userdata.complete_step("setheight")
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname} is now {userdata.height:mu} tall.")

        await nickmanager.nick_update(ctx.author)
        await show_next_step(ctx, userdata, completed=completed_registration)

    @commands.command(
        usage = "<scale>",
        category = "set"
    )
    @commands.guild_only()
    async def setscale(self, ctx: BotContext, *, newscale: Annotated[Decimal, parse_scale] | Literal["banana"]):
        """Change height by scale."""

        if newscale == "banana":
            await ctx.send("Bananas are already the default scale for all things. 🍌")
            logger.log(EGG, "Bananas used for scale.")
            return

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.height = userdata.baseheight * newscale
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname} is now {userdata.height:mu} tall.")

        await nickmanager.nick_update(ctx.author)
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["setheightso", "setscaleso", "setsizeso"],
        usage = "<from> <to>",
        category = "set"
    )
    @commands.guild_only()
    async def setso(self, ctx: BotContext, sv1: discord.Member | SV, sv2: SV):
        """Change height by scale."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        if isinstance(sv1, discord.Member):
            sv1 = userdb.load(sv1.guild.id, ctx.author.id).height  # This feels like a hack. Is this awful?
        userdata.scale = sv1 / sv2
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname} is now {userdata.height:mu} tall.")

        await nickmanager.nick_update(ctx.author)
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["copysize"],
        usage = "<user> [factor]",
        category = "set"
    )
    @commands.guild_only()
    async def copyheight(self, ctx: BotContext, from_user: discord.Member, *, newscale: Annotated[Decimal, parse_scale] = Decimal(1)):
        """Be the size of another user, modified by a factor.

        Examples:
        `&copyheight @User`
        `&copyheight @User 10`
        """
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        from_userdata = userdb.load(ctx.guild.id, from_user.id)
        userdata.height = from_userdata.height * newscale
        completed_registration = userdata.complete_step("setheight")
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname} is now {userdata.height:mu} tall.")

        await nickmanager.nick_update(ctx.author)
        await show_next_step(ctx, userdata, completed=completed_registration)

    @commands.command(
        aliases = ["resetsize", "reset", "resetscale"],
        category = "set"
    )
    @commands.guild_only()
    async def resetheight(self, ctx: BotContext):
        """Reset height/size."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.height = userdata.baseheight
        userdb.save(userdata)

        await ctx.send(f"{ctx.author.display_name} reset their size.")

        await nickmanager.nick_update(ctx.author)
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["setrandomsize"],
        usage = "<minheight> <maxheight>",
        category = "set"
    )
    @commands.guild_only()
    async def setrandomheight(self, ctx: BotContext, minheight: SV, maxheight: SV):
        """Change height to a random value.

        Sets your height to a height between `minheight` and `maxheight`.
        Weighted on a logarithmic curve."""

        if minheight < 0:
            minheight = SV(0)
        if maxheight < 0:
            maxheight = SV(0)

        newheightSV = randrange_log(minheight, maxheight)

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.height = newheightSV
        completed_registration = userdata.complete_step("setheight")
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname} is now {userdata.height:mu} tall.")

        await nickmanager.nick_update(ctx.author)
        await show_next_step(ctx, userdata, completed=completed_registration)

    @commands.command(
        usage = "<minscale> <maxscale>",
        category = "set"
    )
    @commands.guild_only()
    async def setrandomscale(self, ctx: BotContext, minscale: Annotated[Decimal, parse_scale], maxscale: Annotated[Decimal, parse_scale]):
        """Change scale to a random value."""
        if minscale < 0:
            minscale = Decimal(0)
        if maxscale < 0:
            minscale = Decimal(0)

        newscale = Decimal(randrange_log(float(minscale), float(maxscale)))

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.scale = newscale
        completed_registration = userdata.complete_step("setheight")
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname} is now {userdata.height:mu} tall.")

        await nickmanager.nick_update(ctx.author)
        await show_next_step(ctx, userdata, completed=completed_registration)

    @commands.command(
        aliases = ["inf"],
        category = "set"
    )
    @commands.guild_only()
    async def setinf(self, ctx: BotContext):
        """Change height to infinity."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.height = SV("infinity")
        completed_registration = userdata.complete_step("setheight")
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname} is now infinitely tall.")

        await nickmanager.nick_update(ctx.author)
        await show_next_step(ctx, userdata, completed=completed_registration)

    @commands.command(
        aliases = ["0"],
        category = "set"
    )
    @commands.guild_only()
    async def set0(self, ctx: BotContext):
        """Change height to a zero."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.height = 0
        completed_registration = userdata.complete_step("setheight")
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname} is now nothing.")

        await nickmanager.nick_update(ctx.author)
        await show_next_step(ctx, userdata, completed=completed_registration)

    @commands.command(
        usage = "<weight>",
        category = "set"
    )
    async def setweight(self, ctx: BotContext, *, newweight: WV):
        """Set your current weight."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        currweight = newweight
        baseweight = currweight / (userdata.scale ** 3)
        userdata.baseweight = baseweight
        completed_registration = userdata.complete_step("setweight")
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s weight is now {currweight:mu}")

        await nickmanager.nick_update(ctx.author)
        await show_next_step(ctx, userdata, completed=completed_registration)

    @commands.command(
        usage = "<foot>",
        category = "set"
    )
    async def setfoot(self, ctx: BotContext, *, newfoot: Annotated[SV, pos_SV]):
        """Set your current foot length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        currfoot = newfoot
        basefoot = SV(currfoot / userdata.scale)
        userdata.footlength = basefoot
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s base foot length is now {basefoot:mu} long ({to_shoe_size(basefoot, 'm')}), "
                       f"or {currfoot:mu} currently. {to_shoe_size(currfoot, 'm')}")
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["setshoesize"],
        usage = "<shoe>",
        category = "set"
    )
    async def setshoe(self, ctx: BotContext, *, newshoe: str):
        """Set your current shoe size.

        Accepts a US Shoe Size.
        If a W is in the shoe size anywhere, it is parsed as a Women's size.
        If a C is in the show size anywhere, it is parsed as a Children's size.

        Examples:
        `&setshoe 9`
        `&setshoe 10W`
        `&setshoe 12C`
        """
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        currfoot = from_shoe_size(newshoe)
        basefoot = SV(currfoot / userdata.scale)
        userdata.footlength = basefoot
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s base foot length is now {basefoot:mu} long ({to_shoe_size(basefoot, 'm')}), "
                       f"or {currfoot:mu} currently. {to_shoe_size(SV(currfoot), 'm')}")
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["clearfoot", "unsetfoot"],
        category = "set"
    )
    @commands.guild_only()
    async def resetfoot(self, ctx: BotContext):
        """Remove custom foot length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.footlength = None
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s foot length is now default.")
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["pawtoggle"],
        category = "set"
    )
    @commands.guild_only()
    async def togglepaw(self, ctx: BotContext):
        """Switch between the word "foot" and "paw" for your stats."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.pawtoggle = not userdata.pawtoggle
        userdb.save(userdata)

        await ctx.send(f"The end of {userdata.nickname}'s legs are now called a {userdata.footname.lower()}.")
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["furtoggle"],
        category = "set"
    )
    @commands.guild_only()
    async def togglefur(self, ctx: BotContext):
        """Switch between the word "hair" and "fur" for your stats."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.furtoggle = not userdata.furtoggle
        userdb.save(userdata)

        await ctx.send(f"The hair of {userdata.nickname} is now called {userdata.hairname.lower()}.")
        await show_next_step(ctx, userdata)

    @commands.command(
        usage = "<hair>",
        category = "set"
    )
    async def sethair(self, ctx: BotContext, *, newhair: Annotated[SV, pos_SV]):
        """Set your current hair length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.hairlength = SV(newhair / userdata.scale)
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s base hair length is now {userdata.hairlength:mu} long, "
                       f"or {SV(userdata.hairlength):mu} currently.")
        await show_next_step(ctx, userdata)

    @commands.command(
        usage = "<tail>",
        category = "set"
    )
    async def settail(self, ctx: BotContext, *, newtail: Annotated[SV, pos_SV]):
        """Set your current tail length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.taillength = SV(newtail / userdata.scale)
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s base tail length is now {userdata.taillength:mu} long, "
                       f"or {SV(userdata.taillength):mu} currently.")
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["cleartail", "unsettail"],
        category = "set"
    )
    @commands.guild_only()
    async def resettail(self, ctx: BotContext):
        """Remove custom tail length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.taillength = None
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s tail length is now cleared.")
        await show_next_step(ctx, userdata)

    @commands.command(
        usage = "<ear>",
        category = "set"
    )
    async def setear(self, ctx: BotContext, *, newear: Annotated[SV, pos_SV]):
        """Set your current ear heightear."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        currear = newear
        baseear = SV(currear / userdata.scale)
        userdata.earheight = baseear
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s base ear height is now {baseear:mu} long, "
                       f"or {currear:mu} currently.")
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["clearear", "unsetear"],
        category = "set"
    )
    @commands.guild_only()
    async def resetear(self, ctx: BotContext):
        """Remove custom ear height."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.earheight = None
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s ear height is now cleared.")
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["setlift"],
        usage = "<weight>",
        category = "set"
    )
    async def setstrength(self, ctx: BotContext, *, newstrength: Annotated[WV, pos_WV]):
        """Set your current lift/carry strength."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        currstrength = newstrength
        basestrength = WV(currstrength / (userdata.scale ** 3))
        userdata.liftstrength = basestrength
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s base lift strength is now {basestrength:mu}, "
                       f"or {currstrength:mu} currently.")
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["clearstrength", "unsetstrength"],
        category = "set"
    )
    @commands.guild_only()
    async def resetstrength(self, ctx: BotContext):
        """Remove custom lift/carry strength."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.liftstrength = None
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s lift/carry strength is now cleared.")
        await show_next_step(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "set"
    )
    async def setwalk(self, ctx: BotContext, *, newspeed: LinearRate):
        """Set your current walk speed."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        currspeed = SV(newspeed.addPerSec * HOUR)
        basespeed = SV(currspeed / userdata.scale)
        userdata.walkperhour = basespeed
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s base walk speed is now {basespeed:mu} per hour. (Current speed is {currspeed:mu} per hour)")
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["clearwalk", "unsetwalk"],
        category = "set"
    )
    @commands.guild_only()
    async def resetwalk(self, ctx: BotContext):
        """Remove custom walk speed."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.walkperhour = None
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s walk speed is now cleared.")
        await show_next_step(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "set"
    )
    async def setrun(self, ctx: BotContext, *, newspeed: LinearRate):
        """Set your current run speed."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        currspeed = SV(newspeed.addPerSec * HOUR)
        basespeed = SV(currspeed / userdata.scale)
        userdata.runperhour = basespeed
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s base run speed is now {basespeed:mu} per hour. (Current speed is {currspeed:mu} per hour)")
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["clearrun", "unsetrun"],
        category = "set"
    )
    @commands.guild_only()
    async def resetrun(self, ctx: BotContext):
        """Remove custom run speed."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.runperhour = None
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s run speed is now cleared.")
        await show_next_step(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "set"
    )
    async def setswim(self, ctx: BotContext, *, newspeed: LinearRate):
        """Set your current swim speed."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        currspeed = SV(newspeed.addPerSec * HOUR)
        basespeed = SV(currspeed / userdata.scale)
        userdata.swimperhour = basespeed
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s base swim speed is now {basespeed:mu} per hour. (Current speed is {currspeed:mu} per hour)")
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["clearswim", "unsetswim"],
        category = "set"
    )
    @commands.guild_only()
    async def resetswim(self, ctx: BotContext):
        """Remove custom swim speed."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.swimperhour = None
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s swim speed is now cleared.")
        await show_next_step(ctx, userdata)

    @commands.command(
        usage = "<male/female/none>",
        category = "set"
    )
    @commands.guild_only()
    async def setgender(self, ctx: BotContext, gender: Annotated[Gender, parse_gender]):
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.gender = gender
        userdb.save(userdata)

        await nickmanager.nick_update(ctx.author)

        await ctx.send(f"{userdata.nickname}'s gender is now set to {userdata.gender}.")
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["cleargender", "unsetgender"],
        category = "set"
    )
    @commands.guild_only()
    async def resetgender(self, ctx: BotContext):
        """Reset gender."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.gender = None
        userdb.save(userdata)

        await nickmanager.nick_update(ctx.author)

        await ctx.send(f"{userdata.nickname}'s gender is now reset.")
        await show_next_step(ctx, userdata)

    # Admin Commands
    @commands.command(
        category = "mod",
        hidden = True
    )
    @commands.guild_only()
    @commands.is_owner()
    async def setmodel(self, ctx: BotContext, user: discord.Member, *, model: str):
        userdata = userdb.load(ctx.guild.id, user.id)
        userdata.macrovision_model = model
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s model is now {model}.")

    @commands.command(
        aliases = ["resetmodel", "unsetmodel"],
        category = "mod",
        hidden = True
    )
    @commands.guild_only()
    @commands.is_owner()
    async def clearmodel(self, ctx: BotContext, *, user: discord.Member):
        userdata = userdb.load(ctx.guild.id, user.id)
        userdata.macrovision_model = None
        userdb.save(userdata)

        await ctx.send(f"Cleared {userdata.nickname}'s model.")

    @commands.command(
        category = "mod",
        hidden = True
    )
    @commands.guild_only()
    @commands.is_owner()
    async def setview(self, ctx: BotContext, user: discord.Member, *, view: str):
        userdata = userdb.load(ctx.guild.id, user.id)
        userdata.macrovision_view = view
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s view is now {view}.")

    @commands.command(
        aliases = ["resetview", "unsetview"],
        category = "mod",
        hidden = True
    )
    @commands.guild_only()
    @commands.is_owner()
    async def clearview(self, ctx: BotContext, *, user: discord.Member):
        userdata = userdb.load(ctx.guild.id, user.id)
        userdata.macrovision_view = None
        userdb.save(userdata)

        await ctx.send(f"Cleared {userdata.nickname}'s view.")


async def setup(bot: commands.Bot):
    await bot.add_cog(SetCog(bot))
