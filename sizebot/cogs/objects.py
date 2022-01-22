import logging
import math
import random
import typing

import discord
from discord import Embed
from discord.ext import commands
from discord.ext.commands.converter import MemberConverter

from sizebot import __version__
from sizebot.lib import objs, proportions, telemetry, userdb, utils
from sizebot.lib.constants import emojis
from sizebot.lib.errors import InvalidSizeValue
from sizebot.lib.fakeplayer import FakePlayer
from sizebot.lib.loglevels import EGG
from sizebot.lib.objs import DigiObject, objects, tags
from sizebot.lib.units import SV, WV
from sizebot.lib.userdb import load_or_fake
from sizebot.lib.utils import glitch_string, parseMany
from sizebot.lib.versioning import release_on


logger = logging.getLogger("sizebot")


class ObjectsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases = ["objects", "objlist", "objectlist"],
        category = "objects"
    )
    async def objs(self, ctx):
        """Get a list of the various objects SizeBot accepts."""
        objectunits = []
        for obj in objs.objects:
            objectunits.append(obj.name)

        objectunits.sort()

        # TODO: Make this a paged message

        embed = Embed(title=f"Objects [SizeBot {__version__}]", description = f"*NOTE: All of these objects have multiple aliases. If there is an alias that you think should work for a listed object but doesn't, report it with `{ctx.prefix}suggestobject` and note that it's an alias.*")

        for n, units in enumerate(utils.chunkList(objectunits, math.ceil(len(objectunits) / 6))):
            embed.add_field(name="Objects" if n == 0 else "\u200b", value="\n".join(units))

        await ctx.send(embed=embed)

    @commands.command(
        aliases = ["natstats"],
        category = "objects"
    )
    @commands.guild_only()
    async def lookslike(self, ctx, *, memberOrHeight: typing.Union[discord.Member, FakePlayer, SV] = None):
        """See how tall you are in comparison to an object."""
        if memberOrHeight is None:
            memberOrHeight = ctx.author

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight).save()

        userdata = load_or_fake(memberOrHeight)

        if userdata.height == 0:
            await ctx.send(f"{userdata.tag} is really {userdata.height:,.3mu}, or about... huh. I can't find them.")
            return

        goodheightout = userdata.height.toGoodUnit('o', preferName=True, spec=".2%4")
        goodweightout = userdata.weight.toGoodUnit('o', preferName=True, spec=".2%4")

        await ctx.send(f"{userdata.tag} is really {userdata.height:,.3mu}, or about **{goodheightout}**. They weigh about **{goodweightout}**.")

    @commands.command(
        aliases = ["objcompare", "objcomp"],
        usage = "<object/user> [as user/height]",
        category = "objects"
    )
    @commands.guild_only()
    async def objectcompare(self, ctx, *, args: str):
        """See what an object looks like to you.

        Used to see how an object would look at your scale.
        Examples:
        `&objectcompare lego`
        `&objcompare moon as @Kelly`
        """

        argslist = args.rsplit(" as ", 1)
        if len(argslist) == 1:
            what = argslist[0]
            who = None
        else:
            what = argslist[0]
            who = argslist[1]

        mc = MemberConverter()

        what = await parseMany(ctx, what, [DigiObject, mc, SV])
        who = await parseMany(ctx, who, [mc, SV])

        if who is None:
            what = await parseMany(ctx, args, [DigiObject, mc, SV])
            who = ctx.author

        if isinstance(who, SV):
            telemetry.SizeViewed(who).save()

        userdata = load_or_fake(who)
        userstats = proportions.PersonStats(userdata)

        if isinstance(what, DigiObject):
            oc = what.relativestatsembed(userdata)
            await ctx.send(embed = oc)
            return
        elif isinstance(what, discord.Member) or isinstance(what, SV):  # TODO: Make this not literally just a compare. (make one sided)
            compdata = load_or_fake(what)
        elif isinstance(what, str) and what in ["person", "man", "average", "average person", "average man", "average human", "human"]:
            compheight = userstats.avgheightcomp
            compdata = load_or_fake(compheight)
        else:
            telemetry.UnknownObject(str(what)).save()
            await ctx.send(f"`{what}` is not a valid object, member, or height.")
            return
        stats = proportions.PersonComparison(userdata, compdata)
        embedtosend = await stats.toEmbed(ctx.author.id)
        await ctx.send(embed = embedtosend)

    @commands.command(
        aliases = ["look", "examine"],
        usage = "<object>",
        category = "objects"
    )
    @commands.guild_only()
    async def lookat(self, ctx, *, what: typing.Union[DigiObject, discord.Member, FakePlayer, SV, str]):
        """See what an object looks like to you.

        Used to see how an object would look at your scale.
        Examples:
        `&lookat man`
        `&look book`
        `&examine building`"""

        if isinstance(what, SV):
            telemetry.SizeViewed(what).save()

        userdata = load_or_fake(ctx.author)

        if userdata.incomprehensible:
            await ctx.send(glitch_string("hey now, you're an all star, get your game on, go play"))
            return

        if isinstance(what, str):
            what = what.lower()

        if isinstance(what, DigiObject):
            telemetry.ObjectUsed(str(what)).save()
            la = what.relativestatssentence(userdata)
            # Easter eggs.
            if what.name == "photograph":
                la += "\n\n<https://www.youtube.com/watch?v=BB0DU4DoPP4>"
                logger.log(EGG, f"{ctx.author.display_name} is jamming to Nickleback.")
            if what.name == "enderman":
                la += f"\n\n`{ctx.author.display_name} was slain by an Enderman.`"
                logger.log(EGG, f"{ctx.author.display_name} was slain by an Enderman.")
            await ctx.send(la)
            return
        elif isinstance(what, discord.Member) or isinstance(what, SV):  # TODO: Make this not literally just a compare. (make a sentence)
            compdata = load_or_fake(what)
        elif isinstance(what, str) and what.lower() in ["person", "man", "average", "average person", "average man", "average human", "human"]:
            compheight = userdb.defaultheight
            compdata = load_or_fake(compheight, nickname = "an average person")
        elif isinstance(what, str) and what.lower() in ["chocolate", "stuffed animal", "stuffed beaver", "beaver"]:
            logger.log(EGG, f"{ctx.author.display_name} found Chocolate!")
            compdata = load_or_fake(SV.parse("11in"), nickname = "Chocolate [Stuffed Beaver]")
            compdata.baseweight = WV.parse("4.8oz")
            compdata.footlength = SV.parse("2.75in")
            compdata.taillength = SV.parse("12cm")
        elif isinstance(what, str) and what.lower() in ["me", "myself"]:
            compdata = userdb.load(ctx.guild.id, ctx.author.id)
        else:
            # Easter eggs.
            if what.lower() in ["all those chickens", "chickens"]:
                await ctx.send("https://www.youtube.com/watch?v=NsLKQTh-Bqo")
                logger.log(EGG, f"{ctx.author.display_name} looked at all those chickens.")
                return
            if what.lower() == "that horse":
                await ctx.send("https://www.youtube.com/watch?v=Uz4bW2yOLXA")
                logger.log(EGG, f"{ctx.author.display_name} looked at that horse (it may in fact be a moth.)")
                return
            if what.lower() == "my horse":
                await ctx.send("https://www.youtube.com/watch?v=o7cCJqya7wc")
                logger.log(EGG, f"{ctx.author.display_name} looked at my horse (my horse is amazing.)")
                return
            if what.lower() == "cake":
                await ctx.send("The cake is a lie.")
                logger.log(EGG, f"{ctx.author.display_name} realized the cake was lie.")
                return
            if what.lower() == "snout":
                await ctx.send("https://www.youtube.com/watch?v=k2mFvwDTTt0")
                logger.log(EGG, f"{ctx.author.display_name} took a closer look at that snout.")
                return
            await ctx.send(
                f"Sorry, I don't know what `{what}` is.\n"
                f"If this is an object or alias you'd like added to SizeBot, "
                f"use `{ctx.prefix}suggestobject` to suggest it "
                f"(see `{ctx.prefix}help suggestobject` for instructions on doing that.)"
            )
            telemetry.UnknownObject(str(what)).save()
            return
        stats = proportions.PersonComparison(userdata, compdata)
        embedtosend = await stats.toSimpleEmbed(requesterID = ctx.message.author.id)
        await ctx.send(embed = embedtosend)

    @commands.command(
        aliases = ["objectstats"],
        usage = "<object>",
        category = "objects"
    )
    async def objstats(self, ctx, *, what: typing.Union[DigiObject, str]):
        """Get stats about an object.

        Example:
        `&objstats book`"""

        if isinstance(what, str):
            telemetry.UnknownObject(str(what)).save()
            await ctx.send(f"`{what}` is not a valid object.")
            return

        await ctx.send(embed = what.statsembed())

    @release_on("3.7")
    @commands.command(
        category = "objects",
        usage = "[@User]"
    )
    # TODO: Bad name.
    async def stackup(self, ctx, *, who: typing.Union[discord.Member, FakePlayer] = None):
        """How do you stack up against objects?

        Example:
        `&stackup`
        `&stackup @User`
        """

        if who is None:
            who = ctx.author
        userdata = userdb.load_or_fake(who)
        height = userdata.height
        objs_smaller = [o for o in objects if o.unitlength <= height][-3:]
        objs_larger = [o for o in objects if o.unitlength > height][:3]
        names = [o.name for o in objs_smaller] + [userdata.nickname] + [o.name for o in objs_larger]
        heights = [o.unitlength for o in objs_smaller] + [height] + [o.unitlength for o in objs_larger]
        max_name_length = max(len(n) for n in names)
        outstrings = ["```\n"]
        for name, height in zip(names, heights):
            outstrings.append(f"{name:<{max_name_length}} | {height:,.3mu}")
        outstrings.append("```")
        embed = discord.Embed(
            title = f"Object Stackup against {userdata.nickname}",
            description = "\n".join(outstrings))
        await ctx.send(embed = embed)

    @release_on("3.7")
    @commands.command(
        category = "objects"
    )
    async def food(self, ctx, food: typing.Union[DigiObject, str], *, who: typing.Union[discord.Member, FakePlayer, SV] = None):
        """How much food does a person need to eat?

        Takes optional argument of a user to get the food for.

        Example:
        `&food random`
        `&food pizza`
        `&food @User random`
        `&food @User pizza`"""

        CAL_PER_DAY = 2000
        # CAL_PER_MEAL = CAL_PER_DAY / 3
        foods = objs.food

        # Input validation.
        if isinstance(food, DigiObject) and "food" not in food.tags:
            await ctx.send(f"{emojis.error} `{food.name}` is not a food.")
            return

        if who is None:
            who = ctx.author

        userdata = userdb.load_or_fake(who)
        scale = userdata.scale
        scale3 = scale ** 3
        cals_needed = CAL_PER_DAY * scale3

        if food == "random":
            if scale >= 1:
                # TODO: Not a good way to do this.
                foods = foods[-6:]
            food = random.choice(foods)

        days_per_food = food.calories / cals_needed
        food_per_day = 1 / days_per_food

        if food_per_day >= 1:
            foodout = f"{userdata.nickname} would need to eat **{food_per_day:,.1} {food.namePlural}** per day."
        else:
            foodout = f"A {food.name} would last {userdata.nickname} **{days_per_food:,.1} days.**"

        cal_per_day_string = f"{cals_needed:,.0} calories" if cals_needed > 1 else f"less than 1 calorie"

        embed = discord.Embed(
            title = f"{userdata.nickname} eating {food.name}",
            description = foodout)
        embed.set_footer(text = f"{userdata.nickname} needs {cal_per_day_string} per day.")

        await ctx.send(embed = embed)

    @release_on("3.7")
    @commands.command(
        category = "objects"
    )
    async def land(self, ctx, land: typing.Union[DigiObject, str], *, who: typing.Union[discord.Member, FakePlayer, SV] = None):
        """Get stats about how you cover land.

        Example:
        `&land random`
        `&land Australia`
        `&land @User random`
        `&land @User Australia`"""

        lands = objs.land

        # Input validation.
        if isinstance(land, DigiObject) and "land" not in land.tags:
            await ctx.send(f"{emojis.error} `{land.name}` is not land.")
            return

        if who is None:
            who = ctx.author

        userdata = userdb.load_or_fake(who)
        stats = proportions.PersonStats(userdata)
        scale = userdata.scale

        if land == "random":
            land = random.choice(lands)

        if not isinstance(land, DigiObject):
            raise InvalidSizeValue(land, "object")

        land_width = SV(land.width / scale)
        land_length = SV(land.length / scale)
        land_height = SV(land.height / scale)
        fingertip_name = "paw bean" if userdata.pawtoggle else "fingertip"

        land_area = land.width * land.height
        lay_percentage = (stats.height * stats.width) / land_area
        foot_percentage = (stats.footlength * stats.footwidth) / land_area
        finger_percentage = (stats.fingertiplength * stats.fingertiplength) / land_area

        landout = (f"To {userdata.nickname}, {land.name} looks **{land_width:,.3mu}** wide and **{land_length:,.3mu}** long. The highest peak looks **{land_height:,.3mu}** tall. ({land.note})\n\n"
                   f"Laying down, {userdata.nickname} would cover **{lay_percentage:,.2}%** of the land.\n"
                   f"{emojis.blank}({stats.height:,.3mu} tall and {stats.width:,.3mu} wide)\n"
                   f"{userdata.nickname}'s {userdata.footname.lower()} would cover **{foot_percentage:,.2}%** of the land.\n"
                   f"{emojis.blank}({stats.footlength:,.3mu} long and {stats.footwidth:,.3mu} wide)\n"
                   f"{userdata.nickname}'s {fingertip_name} would cover **{finger_percentage:,.2}%** of the land.\n"
                   f"{emojis.blank}({stats.fingertiplength:,.3mu} long and wide)")

        embed = discord.Embed(
            title = f"{userdata.nickname} on {land.name}",
            description = landout)
        embed.set_footer(text = "Note: some percentages may not be achievable in real life due to overhang or strangely shaped landmasses. Consider these calculations to be of optimal maximums.")

        await ctx.send(embed = embed)

    @commands.command(
        category = "objects"
    )
    async def tags(self, ctx):
        """Get the list of object tags."""

        out = "__**Object Tags**__"

        for tag in sorted(tags, key=tags.get, reverse=True):
            if tags[tag] <= 1:
                break
            out += f"\n**{tag}**: {tags[tag]}"

        await ctx.send(out)


def setup(bot):
    bot.add_cog(ObjectsCog(bot))
