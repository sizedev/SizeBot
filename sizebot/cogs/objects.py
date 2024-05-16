from decimal import Decimal
import logging
import math
import random

import discord
from discord import Embed
from discord.ext import commands
from discord.ext.commands.converter import MemberConverter

from sizebot import __version__
from sizebot.lib import objs, proportions, userdb, utils
from sizebot.lib.constants import emojis
from sizebot.lib.errors import InvalidSizeValue
from sizebot.lib.fakeplayer import FakePlayer
from sizebot.lib.loglevels import EGG
from sizebot.lib.objs import DigiObject, objects, tags, format_close_object_smart
from sizebot.lib.stats import StatBox, taglist
from sizebot.lib.units import SV, WV, AV
from sizebot.lib.userdb import load_or_fake, DEFAULT_HEIGHT as AVERAGE_HEIGHT
from sizebot.lib.utils import parse_many, pretty_time_delta, sentence_join


logger = logging.getLogger("sizebot")


class ObjectsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases = ["objects", "objlist", "objectlist"],
        category = "objects",
        usage = "[tag]"
    )
    async def objs(self, ctx: commands.Context, tag: str = None):
        """Get a list of the various objects SizeBot accepts."""
        objectunits = []
        for obj in objs.objects:
            if tag is not None:
                if tag in obj.tags:
                    objectunits.append(obj.name)
            else:
                objectunits.append(obj.name)

        objectunits.sort()

        # TODO: Make this a paged message

        embed = Embed(title=f"Objects [SizeBot {__version__}]", description = f"*NOTE: All of these objects have multiple aliases. If there is an alias that you think should work for a listed object but doesn't, report it with `{ctx.prefix}suggestobject` and note that it's an alias.*")

        for n, units in enumerate(utils.chunk_list(objectunits, math.ceil(len(objectunits) / 6))):
            embed.add_field(name="Objects" if n == 0 else "\u200b", value="\n".join(units))

        await ctx.send(embed=embed)

    @commands.command(
        aliases = ["natstats"],
        category = "objects"
    )
    @commands.guild_only()
    async def lookslike(self, ctx: commands.Context, *, memberOrHeight: discord.Member | FakePlayer | SV = None):
        """See how tall you are in comparison to an object."""
        if memberOrHeight is None:
            memberOrHeight = ctx.author

        userdata = load_or_fake(memberOrHeight)

        if userdata.height == 0:
            await ctx.send(f"{userdata.tag} is really {userdata.height:,.3mu}, or about... huh. I can't find them.")
            return

        goodheightout = format_close_object_smart(userdata.height)
        goodweightout = format_close_object_smart(userdata.weight)

        await ctx.send(f"{userdata.tag} is really {userdata.height:,.3mu}, or about **{goodheightout}**. They weigh about **{goodweightout}**.")

    @commands.command(
        aliases = ["objcompare", "objcomp"],
        usage = "<object/user> [as user/height]",
        category = "objects"
    )
    @commands.guild_only()
    async def objectcompare(self, ctx: commands.Context, *, args: str):
        """See what an object looks like to you.

        Used to see how an object would look at your scale.
        Examples:
        `&objectcompare lego`
        `&objcompare moon to @Kelly`
        """

        argslist = args.rsplit(" to ", 1)
        if len(argslist) == 1:
            what = argslist[0]
            who = None
        else:
            what = argslist[0]
            who = argslist[1]

        mc = MemberConverter()

        what = await parse_many(ctx, what, [DigiObject, mc, SV])
        who = await parse_many(ctx, who, [mc, SV])

        if who is None:
            what = await parse_many(ctx, args, [DigiObject, mc, SV])
            who = ctx.author

        userdata = load_or_fake(who)
        userstats = StatBox.load(userdata.stats).scale(userdata.scale)

        if isinstance(what, DigiObject):
            oc = what.relativestatsembed(userdata)
            await ctx.send(embed = oc)
            return
        elif isinstance(what, discord.Member) or isinstance(what, SV):  # TODO: Make this not literally just a compare. (make one sided)
            compdata = load_or_fake(what)
        elif isinstance(what, str) and what in ["person", "man", "average", "average person", "average man", "average human", "human"]:
            compheight = userstats['averagescale'].value
            compdata = load_or_fake(compheight)
        else:
            await ctx.send(f"`{what}` is not a valid object, member, or height.")
            return
        tosend = proportions.get_compare(userdata, compdata, ctx.author.id)
        await ctx.send(**tosend)

    @commands.command(
        aliases = ["look", "examine"],
        usage = "<object>",
        category = "objects"
    )
    @commands.guild_only()
    async def lookat(self, ctx: commands.Context, *, what: DigiObject | discord.Member | FakePlayer | SV | str):
        """See what an object looks like to you.

        Used to see how an object would look at your scale.
        Examples:
        `&lookat man`
        `&look book`
        `&examine building`"""

        userdata = load_or_fake(ctx.author)

        if isinstance(what, str):
            what = what.lower()

        # TODO: Should easter eggs be in a different place?

        # Compare to registered DigiObject by string name
        if isinstance(what, DigiObject):
            la = what.relativestatssentence(userdata)
            # Easter eggs.
            eggs = {
                "photograph": ("<https://www.youtube.com/watch?v=BB0DU4DoPP4>", f"{ctx.author.display_name} is jamming to Nickleback."),
                "enderman": (f"`{ctx.author.display_name} was slain by an Enderman.`", f"{ctx.author.display_name} was slain by an Enderman.")
            }
            if what.name in eggs:
                msg, logmsg = eggs[what.name]
                la += "\n\n" + msg
                logger.log(EGG, logmsg)
            await ctx.send(la)
            return

        # Member comparisons are just height comparisons
        if isinstance(what, (discord.Member, FakePlayer)):
            compdata = load_or_fake(what)
            what = compdata.height

        # Height comparisons
        if isinstance(what, SV):
            height = SV(what * userdata.viewscale)
            s = (f"{userdata.nickname} is {userdata.height:,.1{userdata.unitsystem}} tall."
                 f" To them, {what:,.1mu} looks like **{height:,.1mu}**."
                 f" That's about **{height.to_best_unit('o', preferName=True, spec=".1")}**.")
            await ctx.send(s)
            return

        # Easter Eggs
        eggs = {
            "all those chickens": ("https://www.youtube.com/watch?v=NsLKQTh-Bqo", f"{ctx.author.display_name} looked at all those chickens."),
            "chickens": ("https://www.youtube.com/watch?v=NsLKQTh-Bqo", f"{ctx.author.display_name} looked at all those chickens."),
            "that horse": ("https://www.youtube.com/watch?v=Uz4bW2yOLXA", f"{ctx.author.display_name} looked at that horse (it may in fact be a moth.)"),
            "my horse": ("https://www.youtube.com/watch?v=o7cCJqya7wc", f"{ctx.author.display_name} looked at my horse (my horse is amazing.)"),
            "cake": ("The cake is a lie.", f"{ctx.author.display_name} realized the cake was lie."),
            "snout": ("https://www.youtube.com/watch?v=k2mFvwDTTt0", f"{ctx.author.display_name} took a closer look at that snout."),
        }
        if what in eggs:
            msg, logmsg = eggs[what]
            await ctx.send(msg)
            logger.log(EGG, logmsg)
            return

        average_data = load_or_fake(AVERAGE_HEIGHT, nickname = "an average person")
        choc_data = load_or_fake(SV.parse("11in"), nickname = "Chocolate [Stuffed Beaver]")
        choc_data.baseweight = WV.parse("4.8oz")
        choc_data.footlength = SV.parse("2.75in")
        choc_data.taillength = SV.parse("12cm")
        userdata = userdb.load(ctx.guild.id, ctx.author.id)

        # Comparison command
        comp_keys = {
            "person": average_data,
            "man": average_data,
            "average": average_data,
            "average person": average_data,
            "average man": average_data,
            "average human": average_data,
            "human": average_data,
            "chocolate": choc_data,
            "stuffed animal": choc_data,
            "stuffed beaver": choc_data,
            "beaver": choc_data,
            "me": userdata,
            "myself": userdata
        }
        if what in comp_keys:
            compdata = comp_keys[what]
            tosend = proportions.get_compare_simple(userdata, compdata, ctx.message.author.id)
            await ctx.send(**tosend)
            return

        # Not found
        await ctx.send(
            f"Sorry, I don't know what `{what}` is.\n"
            f"If this is an object or alias you'd like added to SizeBot, "
            f"use `{ctx.prefix}suggestobject` to suggest it "
            f"(see `{ctx.prefix}help suggestobject` for instructions on doing that.)"
        )

    @commands.command(
        aliases = ["objectstats"],
        usage = "<object>",
        category = "objects"
    )
    async def objstats(self, ctx: commands.Context, *, what: DigiObject | str):
        """Get stats about an object.

        Example:
        `&objstats book`"""

        if isinstance(what, str):
            await ctx.send(f"`{what}` is not a valid object.")
            return

        await ctx.send(embed = what.statsembed())

    @commands.command(
        category = "objects",
        usage = "[@User]"
    )
    # TODO: Bad name.
    async def stackup(self, ctx: commands.Context, amount: int | None = None, *, who: discord.Member | FakePlayer | SV = None):
        """How do you stack up against objects?

        Example:
        `&stackup`
        `&stackup @User`
        """

        if who is None:
            who = ctx.author
        if amount is None:
            amount = 3
        userdata = userdb.load_or_fake(who)
        height = userdata.height
        objs_smaller = [o for o in objects if o.unitlength <= height][-amount:]
        objs_larger = [o for o in objects if o.unitlength > height][:amount]
        names = [o.name for o in objs_smaller] + ["[" + userdata.nickname + "]"] + [o.name for o in objs_larger]
        heights = [o.unitlength for o in objs_smaller] + [height] + [o.unitlength for o in objs_larger]
        max_name_length = max(len(n) for n in names)
        outstrings = ["```"]
        for name, height in zip(names, heights):
            outstrings.append(f"{name:<{max_name_length}} | {height:,.3mu}")
        outstrings.append("```\n")
        outstrings.reverse()
        embed = discord.Embed(
            title = f"Object Stackup against {userdata.nickname}",
            description = "\n".join(outstrings))
        await ctx.send(embed = embed)

    @commands.command(
        category = "objects"
    )
    async def food(self, ctx: commands.Context, food: DigiObject | str, *, who: discord.Member | FakePlayer | SV = None):
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

        if isinstance(food, str) and food != "random":
            await ctx.send(f"{emojis.error} `{food}` is not a known object.")
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
        cost = (food.price * food_per_day) if food.price else None

        if food_per_day >= 1:
            foodout = f"{userdata.nickname} would need to eat **{food_per_day:,.1} {food.name_plural}** per day."
            if cost:
                foodout += f"\nThat would cost **${cost:,.2f}**."
            foodout += f"\n(1 {food.name} is {food.calories} calories.)"
        else:
            foodout = f"A {food.name} ({food.calories} calories) would last {userdata.nickname} **{pretty_time_delta(86400 * days_per_food, roundeventually=True)}.**"

        cal_per_day_string = f"{cals_needed:,.0} calories" if cals_needed > 1 else "less than 1 calorie"

        embed = discord.Embed(
            title = f"{userdata.nickname} eating {food.name}",
            description = foodout)
        embed.set_footer(text = f"{userdata.nickname} needs {cal_per_day_string} per day.")

        await ctx.send(embed = embed)

    @commands.command(
        category = "objects"
    )
    async def water(self, ctx: commands.Context, *, who: discord.Member | FakePlayer | SV = None):
        if who is None:
            who = ctx.author

        userdata = userdb.load_or_fake(who)
        scale = userdata.scale

        BASE_WATER = WV(3200)

        water_weight = WV(BASE_WATER * (scale ** 3))
        water_liters = water_weight / 1000
        water_gallons = water_liters / Decimal("3.78541")

        embed = discord.Embed(
            title = f"{userdata.nickname} drinking water",
            description = f"{userdata.nickname} would need to drink **{water_weight:,.3mu}** per day. That's **{water_liters:,.1} liters**, or **{water_gallons:,.1} gallons**.")

        await ctx.send(embed = embed)

    @commands.command(
        category = "objects"
    )
    async def land(self, ctx: commands.Context, land: DigiObject | str, *, who: discord.Member | FakePlayer | SV = None):
        """Get stats about how you cover land.
        #ACC#

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
        stats = StatBox.load(userdata.stats).scale(userdata.scale)
        scale = userdata.scale

        if land == "random":
            land = random.choice(lands)

        if not isinstance(land, DigiObject):
            raise InvalidSizeValue(land, "object")

        land_width = SV(land.width / scale)
        land_length = SV(land.length / scale)
        land_height = SV(land.height / scale)
        fingertip_name = "paw bean" if userdata.pawtoggle else "fingertip"

        land_area = AV(land.width * land.height)
        area = AV(stats['height'].value * stats['width'].value)
        lay_percentage = area / land_area
        foot_area = AV(stats['footlength'].value * stats['footwidth'].value)
        finger_area = AV(stats['fingertiplength'].value * stats['fingertiplength'].value)
        foot_percentage = foot_area / land_area
        finger_percentage = finger_area / land_area

        landout = (f"To {userdata.nickname}, {land.name} looks **{land_width:,.1mu}** wide and **{land_length:,.1mu}** long. ({land_area:,.1mu}) The highest peak looks **{land_height:,.1mu}** tall. ({land.note})\n\n"
                   f"Laying down, {userdata.nickname} would cover **{lay_percentage:,.2}%** of the land.\n"
                   f"{emojis.blank}({stats['height'].value:,.1mu} tall and {stats['width'].value:,.1mu} wide, or {area:,.1mu})\n"
                   f"{userdata.nickname}'s {userdata.footname.lower()} would cover **{foot_percentage:,.2}%** of the land.\n"
                   f"{emojis.blank}({stats['footlength'].value:,.1mu} long and {stats['footwidth'].value:,.1mu} wide, or {foot_area:,.1mu})\n"
                   f"{userdata.nickname}'s {fingertip_name} would cover **{finger_percentage:,.2}%** of the land.\n"
                   f"{emojis.blank}({stats['fingertiplength'].value:,.1mu} long and wide, or {finger_area:,.1mu})")

        embed = discord.Embed(
            title = f"{userdata.nickname} on {land.name}",
            description = landout)
        embed.set_footer(text = "Note: some percentages may not be achievable in real life due to overhang or strangely shaped landmasses. Consider these calculations to be of optimal maximums.")

        await ctx.send(embed = embed)

    @commands.command(
        category = "objects"
    )
    async def tags(self, ctx):
        """Get the list of object and stat tags."""

        out = "__**Stat Tags**__\n"

        stattags = sentence_join([f"`{t}`" for t in taglist])
        out += stattags

        out += "\n\n__**Object Tags**__\n"

        for tag in sorted(tags, key=tags.get, reverse=True):
            if tags[tag] <= 1:
                break
            out += f"`{tag}` ({tags[tag]}), "

        out = out.removesuffix(", ")

        await ctx.send(out)

    @commands.command(
        usage = "[object]",
        category = "objects"
    )
    async def scaled(self, ctx: commands.Context, *, obj: DigiObject):
        userdata = load_or_fake(ctx.author)
        await ctx.send(f"{obj.article.capitalize()} {obj.name} scaled for {userdata.nickname} is {obj.get_stats_sentence(userdata.scale, userdata.unitsystem)}")


async def setup(bot):
    await bot.add_cog(ObjectsCog(bot))
