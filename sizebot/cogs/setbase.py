import logging

from discord.ext import commands

from sizebot.cogs.register import show_next_step
from sizebot.lib import errors, userdb, nickmanager
from sizebot.lib.constants import emojis
from sizebot.lib.diff import LinearRate, Rate
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.shoesize import to_shoe_size, from_shoe_size
from sizebot.lib.stats import HOUR
from sizebot.lib.types import BotContext
from sizebot.lib.units import SV, WV

logger = logging.getLogger("sizebot")


class SetBaseCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        usage = "<height>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbaseheight(self, ctx: BotContext, *, newbaseheight: SV):
        """Change base height."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        # Convenience for initial registration
        if "setbaseheight" in userdata.registration_steps_remaining:
            if not (SV.parse("4ft") < newbaseheight < SV.parse("8ft")):
                await ctx.send(f"{emojis.warning} **WARNING:** Your base height should probably be something more human-scale. This makes comparison math work out much nicer. If this was intended, you can ignore this warning, but it is ***highly recommended*** that you have a base height similar to the size of a normal human being.")

        userdata.baseheight = newbaseheight
        completed_registration = userdata.complete_step("setbaseheight")
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s base height is now {userdata.baseheight:mu} tall.")

        await nickmanager.nick_update(ctx.author)
        await show_next_step(ctx, userdata, completed=completed_registration)

    @commands.command(
        usage = "<weight>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbaseweight(self, ctx: BotContext, *, newbaseweight: WV):
        """Change base weight."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        if "setbaseweight" in userdata.registration_steps_remaining:
            if not (WV.parse("10lb") < newbaseweight < WV.parse("1000lb")):
                await ctx.send(f"{emojis.warning} **WARNING:** Your base weight should probably be something more human-scale. This makes comparison math work out much nicer. If this was intended, you can ignore this warning, but it is ***highly recommended*** that you have a base weight similar to that of a normal human being.")

        userdata.baseweight = newbaseweight
        completed_registration = userdata.complete_step("setbaseweight")
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s base weight is now {userdata.baseweight:mu}")

        await nickmanager.nick_update(ctx.author)
        await show_next_step(ctx, userdata, completed=completed_registration)

    @commands.command(
        usage = "<height/weight> [height/weight]",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbase(self, ctx: BotContext, arg1: SV | WV, arg2: SV | WV = None):
        """Set your base height and weight."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        # Don't allow a user to enter setbase(SV, SV) or setbase(WV, WV)
        if (isinstance(arg1, SV) and isinstance(arg2, SV)) or (isinstance(arg1, WV) and isinstance(arg2, WV)):
            raise errors.UserMessedUpException("Please do not enter two heights or two weights.")

        newbaseheight = None
        newbaseweight = None
        for arg in [arg1, arg2]:
            if isinstance(arg, SV):
                newbaseheight = arg
            if isinstance(arg, WV):
                newbaseweight = arg
        completed_registration = False
        if newbaseheight is not None:
            if "setbaseheight" in userdata.registration_steps_remaining:
                # TODO: Actually have a confirm message here.
                if not (SV.parse("4ft") <= newbaseheight < SV.parse("8ft")):
                    await ctx.send(f"{emojis.warning} **WARNING:** Your base height should probably be something more human-scale. This makes comparison math work out much nicer. If this was intended, you can ignore this warning, but it is ***highly recommended*** that you have a base height similar to the size of a normal human being.")
            userdata.baseheight = newbaseheight
            completed_registration = userdata.complete_step("setbaseheight") or completed_registration
        if newbaseweight is not None:
            if "setbaseweight" in userdata.registration_steps_remaining:
                if not (WV.parse("10lb") <= newbaseheight < SV.parse("1000lb")):
                    await ctx.send(f"{emojis.warning} **WARNING:** Your base weight should probably be something more human-scale. This makes comparison math work out much nicer. If this was intended, you can ignore this warning, but it is ***highly recommended*** that you have a base weight similar to that of a normal human being.")
            userdata.baseweight = newbaseweight
            completed_registration = userdata.complete_step("setbaseweight") or completed_registration
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname} changed their base height and weight to {userdata.baseheight:,.3mu} and {userdata.baseweight:,.3mu}.")
        await show_next_step(ctx, userdata, completed=completed_registration)

    @commands.command(
        usage = "<length>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbasefoot(self, ctx: BotContext, *, newfoot: Decimal | SV):
        """Set a custom foot length."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.footlength = newfoot
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s foot is now {userdata.footlength:mu} long. ({to_shoe_size(userdata.footlength, 'm')})")
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["setbaseshoesize"],
        usage = "<length>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbaseshoe(self, ctx: BotContext, *, newshoe: str):
        """Set a custom base shoe size.

        Accepts a US Shoe Size.
        If a W is in the shoe size anywhere, it is parsed as a Women's size.
        If a C is in the show size anywhere, it is parsed as a Children's size.

        Examples:
        `&setbaseshoe 9`
        `&setbaseshoe 10W`
        `&setbaseshoe 12C`
        """

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        newfoot = from_shoe_size(newshoe)

        userdata.footlength = newfoot
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s foot is now {userdata.footlength:mu} long. ({to_shoe_size(userdata.footlength, 'm')})")
        await show_next_step(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbasehair(self, ctx: BotContext, *, newhair: str):
        """Set a custom base hair length."""
        newhairsv = SV.parse(newhair)

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.hairlength = newhairsv
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s hair is now {userdata.hairlength:mu} long.")
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["clearhair", "unsethair"],
        category = "set"
    )
    @commands.guild_only()
    async def resethair(self, ctx: BotContext):
        """Remove custom hair length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.hairlength = None
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s hair length is now cleared.")
        await show_next_step(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbasetail(self, ctx: BotContext, *, newtail: str):
        """Set a custom tail length."""
        newtailsv = SV.parse(newtail)

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.taillength = newtailsv
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s tail is now {userdata.taillength:mu} long.")
        await show_next_step(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbaseear(self, ctx: BotContext, *, newear: str):
        """Set a custom ear height."""
        newearsv = SV.parse(newear)

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.earheight = newearsv
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s ear is now {userdata.earheight:mu} long.")
        await show_next_step(ctx, userdata)

    @commands.command(
        aliases = ["setbaselift"],
        usage = "<weight>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbasestrength(self, ctx: BotContext, *, newstrength: WV):
        """Set a custom lift/carry strength."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.liftstrength = newstrength
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s strength is now {WV(userdata.liftstrength):mu}.")
        await show_next_step(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbasewalk(self, ctx: BotContext, *, newwalk: Rate):
        """Set a custom walk speed."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.walkperhour = newwalk
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s walk is now {userdata.walkperhour:mu} per hour.")
        await show_next_step(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbaserun(self, ctx: BotContext, *, newrun: Rate):
        """Set a custom run speed."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.runperhour = newrun
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s run is now {userdata.runperhour:mu} per hour.")
        await show_next_step(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "setbase"
    )
    @commands.guild_only()
    async def setbaseswim(self, ctx: BotContext, *, newswim: LinearRate):
        """Set a custom swim speed."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.swimperhour = SV(newswim.addPerSec * HOUR)
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s swim is now {userdata.swimperhour:mu} per hour.")
        await show_next_step(ctx, userdata)


async def setup(bot: commands.Bot):
    await bot.add_cog(SetBaseCog(bot))
