import logging
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.fakeplayer import FakePlayer
from sizebot.lib.freefall import freefall
import typing

import discord
from discord.ext import commands

from sizebot.cogs.register import showNextStep
from sizebot.lib import errors, proportions, userdb, macrovision, telemetry
from sizebot.lib.constants import colors, emojis
from sizebot.lib.language import engine
from sizebot.lib.units import SV, TV
from sizebot.lib.userdb import load_or_fake
from sizebot.lib.utils import glitch_string, pretty_time_delta, sentence_join

logger = logging.getLogger("sizebot")

MemberOrSize = typing.Union[discord.Member, FakePlayer, SV]


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        usage = "[user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def stats(self, ctx, *, memberOrHeight: MemberOrSize = None):
        """User stats command.

        Get tons of user stats about yourself, a user, or a raw height.

        Examples:
        `&stats` (defaults to stats about you.)
        `&stats @User`
        `&stats 10ft`
        """
        if memberOrHeight is None:
            memberOrHeight = ctx.author

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight).save()

        same_user = isinstance(memberOrHeight, discord.Member) and memberOrHeight.id == ctx.author.id
        userdata = load_or_fake(memberOrHeight, allow_unreg = same_user)

        stats = proportions.PersonStats(userdata)

        embedtosend = stats.toEmbed(ctx.author.id)
        await ctx.send(embed = embedtosend)

        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<from> <to> [user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def statsso(self, ctx, sv1: MemberOrSize, sv2: SV, *, memberOrHeight: MemberOrSize = None):
        """Stats so that from looks like to.
        """
        if memberOrHeight is None:
            memberOrHeight = ctx.author

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight).save()

        sv1 = load_or_fake(sv1).height  # This feels like a hack. Is this awful?
        scale_factor = sv1 / sv2

        same_user = isinstance(memberOrHeight, discord.Member) and memberOrHeight.id == ctx.author.id
        userdata = load_or_fake(memberOrHeight, allow_unreg = same_user)
        userdata.scale = scale_factor

        stats = proportions.PersonStats(userdata)

        embedtosend = stats.toEmbed(ctx.author.id)
        await ctx.send(embed = embedtosend)

        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "[user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def basestats(self, ctx, *, member: discord.Member = None):
        """User basestats command.

        Get the base stats about yourself or a user.

        Examples:
        `&sbasetats` (defaults to stats about you.)
        `&basestats @User`
        """
        if member is None:
            member = ctx.author

        userdata = userdb.load(ctx.guild.id, member.id)

        stats = proportions.PersonBaseStats(userdata)

        embedtosend = stats.toEmbed(ctx.author.id)
        await ctx.send(embed = embedtosend)

        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "[user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def statsas(self, ctx, memberOrHeight: MemberOrSize = None,
                      memberOrHeight2: MemberOrSize = None):
        """User stats command with modified bases.

        Get tons of user stats about yourself, a user, or a raw height, as if they were a different height.

        Examples:
        `&statsas 100ft` (defaults to stats about you, if you were a certain height.)
        `&statsas 100ft @User` (get stats about @User if they were a certain height.)
        `&statsas @User @User2` (get stats about @User2 if they were as tall as @User.)
        """
        if memberOrHeight is None:
            raise errors.ArgumentException
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.author

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight).save()
        if isinstance(memberOrHeight2, SV):
            telemetry.SizeViewed(memberOrHeight).save()

        userdata = load_or_fake(memberOrHeight)
        userdata2 = load_or_fake(memberOrHeight2)
        userdata2.nickname = userdata2.nickname + " as " + userdata.nickname
        userdata2.height = userdata.height

        stats = proportions.PersonStats(userdata2)

        embedtosend = stats.toEmbed(ctx.author.id)
        await ctx.send(embed = embedtosend)

    @commands.command(
        aliases = ["get"],
        usage = "<stat> [user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def stat(self, ctx, stat, *, memberOrHeight: MemberOrSize = None):
        """User stat command.

        Get a single stat about yourself, a user, or a raw height.

        Available stats are: #STATS#

        Examples:
        `&stat height` (not specifying a user returns a stat about yourself.)
        `&stat weight @User`
        `&stat foot 10ft`
        """

        if memberOrHeight is None:
            memberOrHeight = ctx.author

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight).save()

        same_user = isinstance(memberOrHeight, discord.Member) and memberOrHeight.id == ctx.author.id
        userdata = load_or_fake(memberOrHeight, allow_unreg = same_user)

        stats = proportions.PersonStats(userdata)

        stattosend = stats.getFormattedStat(stat)

        if stattosend is None:
            await ctx.send(f"The `{stat}` stat is unavailable for this user.")
            return

        await ctx.send(stattosend)
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<from> <to> <stat> [user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def statso(self, ctx, sv1: MemberOrSize, sv2: SV, stat, *, memberOrHeight: MemberOrSize = None):
        """User stat command as if an implied scale.

        Available stats are: #STATS#`
        """

        if memberOrHeight is None:
            memberOrHeight = ctx.author

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight).save()

        same_user = isinstance(memberOrHeight, discord.Member) and memberOrHeight.id == ctx.author.id
        userdata = load_or_fake(memberOrHeight, allow_unreg = same_user)
        sv1 = load_or_fake(sv1).height  # This feels like a hack. Is this awful?
        scale_factor = sv1 / sv2
        userdata.scale = scale_factor

        stats = proportions.PersonStats(userdata)

        stattosend = stats.getFormattedStat(stat)

        if stattosend is None:
            await ctx.send(f"The `{stat}` stat is unavailable for this user.")
            return

        await ctx.send(stattosend)
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["getas"],
        usage = "<stat> [user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def statas(self, ctx, stat, memberOrHeight: MemberOrSize = None,
                     memberOrHeight2: MemberOrSize = None):
        """User stat command with custom bases.

        Get a single stat about yourself, a user, or a raw height, as if they were a different height.

        Available stats are: #STATS#

        Examples:
        `&statas weight 100ft` (defaults to stats about you, if you were a certain height.)
        `&statas foot 100ft @User` (get stats about @User if they were a certain height.)
        `&statas speed @User @User2` (get stats about @User2 if they were as tall as @User.)
        """

        if memberOrHeight is None:
            raise errors.ArgumentException
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.author

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight).save()
        if isinstance(memberOrHeight2, SV):
            telemetry.SizeViewed(memberOrHeight).save()

        userdata = load_or_fake(memberOrHeight)
        userdata2 = load_or_fake(memberOrHeight2)
        userdata2.nickname = userdata2.nickname + " as " + userdata.nickname
        userdata2.height = userdata.height

        stats = proportions.PersonStats(userdata2)

        stattosend = stats.getFormattedStat(stat)

        if stattosend is None:
            await ctx.send(f"The `{stat}` stat is unavailable for this user.")
            return

        await ctx.send(stattosend)

    @commands.command(
        aliases = ["comp", "comparison"],
        usage = "<user/height> [user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def compare(self, ctx, memberOrHeight: MemberOrSize = None,
                      *, memberOrHeight2: MemberOrSize = None):
        """Compare two users' size.

        If give one user, compares you to that user."""
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.author

        if memberOrHeight is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.")
            return

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight).save()
        if isinstance(memberOrHeight2, SV):
            telemetry.SizeViewed(memberOrHeight).save()

        userdata1 = load_or_fake(memberOrHeight)
        userdata2 = load_or_fake(memberOrHeight2)

        msg = await ctx.send(emojis.loading + " *Loading comparison...*")

        comparison = proportions.PersonComparison(userdata1, userdata2)
        embedtosend = await comparison.toEmbed(ctx.author.id)
        await msg.edit(content = "", embed = embedtosend)

    @commands.command(
        aliases = ["compas"],
        usage = "[user/height] [user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def compareas(self, ctx, asHeight: MemberOrSize = None,
                        memberOrHeight: MemberOrSize = None):
        """Compare yourself as a different height and another user."""

        if isinstance(asHeight, SV):
            telemetry.SizeViewed(asHeight).save()
        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight).save()

        userdata = load_or_fake(ctx.message.author)
        asdata = load_or_fake(asHeight)
        userdata.height = asdata.height
        userdata.nickname += " as " + asdata.nickname
        comparedata = load_or_fake(memberOrHeight)

        msg = await ctx.send(emojis.loading + " *Loading comparison...*")

        comparison = proportions.PersonComparison(userdata, comparedata)
        embedtosend = await comparison.toEmbed(ctx.author.id)
        await msg.edit(content = "", embed = embedtosend)

    @commands.command(
        aliases = ["dist", "walk", "run", "climb", "swim", "crawl", "drive"],
        usage = "<length> [user]",
        category = "stats"
    )
    async def distance(self, ctx, memberOrHeightorTime: typing.Union[discord.Member, FakePlayer, SV, TV, str] = None,
                       *, memberOrHeight2: MemberOrSize = None):
        """How long will it take to walk, run, climb, etc. a distance/time?

        If a time is supplied, it is calculated by how much distance you could walk in that time at your base walk speed.

        Example:
        `&distance <length or time> [user]`"""

        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.author

        if memberOrHeightorTime is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.")
            return

        userdata2 = load_or_fake(memberOrHeight2)

        if isinstance(memberOrHeightorTime, str):
            raise errors.InvalidSizeValue(memberOrHeightorTime, "size or time")
        elif isinstance(memberOrHeightorTime, TV):
            walkpersecond = SV(userdata2.walkperhour / 3600) if userdata2.walkperhour else proportions.AVERAGE_WALKPERHOUR / 3600
            walkpersecond *= userdata2.scale
            memberOrHeightorTime = SV(walkpersecond * memberOrHeightorTime)

        if isinstance(memberOrHeightorTime, SV):
            telemetry.SizeViewed(memberOrHeightorTime).save()
        if isinstance(memberOrHeight2, SV):
            telemetry.SizeViewed(memberOrHeight2).save()

        userdata1 = load_or_fake(memberOrHeightorTime)

        if userdata2.height > userdata1.height:
            h = SV(userdata1.height * userdata2.viewscale)
            msg = f"To {userdata2.nickname}, {userdata1.height:,.3mu} appears to be **{h:,.3mu}.**"
            await ctx.send(msg)
            return

        comparison = proportions.PersonSpeedComparison(userdata2, userdata1)
        stat = "height"
        embedtosend = comparison.getStatEmbed(stat)

        if embedtosend is None:
            await ctx.send(f"{userdata1.nickname} doesn't have the `{stat}` stat.")
            return

        embedtosend.title = f"{comparison.viewed.height:,.3mu} to {comparison.viewer.nickname}"
        embedtosend.set_footer(text = f"{comparison.viewed.height:,.3mu} is {comparison.multiplier:,.3}x larger than {comparison.viewer.nickname}.")

        await ctx.send(embed = embedtosend)

    @commands.command(
        aliases = ["diststats"],
        usage = "<user/height> [user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def distancestats(self, ctx, memberOrHeight: MemberOrSize = None,
                            *, memberOrHeight2: MemberOrSize = None):
        """Find how long it would take to travel across a person."""
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.author

        if memberOrHeight is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.")
            return

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight).save()
        if isinstance(memberOrHeight2, SV):
            telemetry.SizeViewed(memberOrHeight2).save()

        userdata1 = load_or_fake(memberOrHeight)
        userdata2 = load_or_fake(memberOrHeight2)

        comparison = proportions.PersonSpeedComparison(userdata2, userdata1)
        embedtosend = await comparison.toEmbed(ctx.author.id)

        if userdata1.incomprehensible or userdata2.incomprehensible:
            ed = embedtosend.to_dict()
            for field in ed["fields"]:
                field["value"] = glitch_string(field["value"])
            embedtosend = discord.Embed.from_dict(ed)
            embedtosend.set_footer(text = glitch_string(embedtosend.footer.text))

        await ctx.send(embed = embedtosend)

    @commands.command(
        aliases = ["diststat"],
        usage = "<stat> <user/height> [user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def distancestat(self, ctx, stat, memberOrHeight: MemberOrSize = None,
                           *, memberOrHeight2: MemberOrSize = None):
        """Find how long it would take to travel across a certain distance on a person.

        Available stats are: #STATS#"""
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.author

        if memberOrHeight is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.")
            return

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight).save()
        if isinstance(memberOrHeight2, SV):
            telemetry.SizeViewed(memberOrHeight2).save()

        userdata1 = load_or_fake(memberOrHeight)
        userdata2 = load_or_fake(memberOrHeight2)

        comparison = proportions.PersonSpeedComparison(userdata2, userdata1)

        embedtosend = comparison.getStatEmbed(stat)

        if embedtosend is None:
            await ctx.send(f"{userdata1.nickname} doesn't have the `{stat}` stat.")
            return

        await ctx.send(embed = embedtosend)

    @commands.command(
        aliases = ["reversedistance", "reversedist", "revdist"],
        usage = "<length> [user]",
        category = "stats"
    )
    async def ruler(self, ctx, length: SV, *, who: MemberOrSize = None):
        """A distance to a user looks how long to everyone else?

        Examples:
        `&ruler 1mi`
        `&ruler 1ft @DigiDuncan`"""

        if who is None:
            who = ctx.message.author

        userdata = load_or_fake(who)
        userstats = proportions.PersonStats(userdata)

        if userdata.height == 0:
            await ctx.send(f"{userdata.tag} doesn't exist...")
            return

        newlength = SV(length / userstats.stats.values["viewscale"])

        desc = f"To everyone else, {userstats.nickname}'s {length:,.3mu} would look to be **{newlength:,.3mu}.**"
        if userdata.incomprehensible:
            desc = glitch_string(desc)

        e = discord.Embed(
            title = f"{userstats.nickname}'s {length:,.3mu} to the world",
            description = desc
        )

        await ctx.send(embed = e)

    @commands.command(
        usage = "<user or length>",
        category = "stats"
    )
    async def sound(self, ctx, *, who: MemberOrSize = None):
        """Find how long it would take sound to travel a length or height."""
        ONE_SOUNDSECOND = SV(340.27)
        is_SV = False

        if who is None:
            who = ctx.message.author

        if isinstance(who, SV):
            is_SV = True

        userdata = load_or_fake(who)
        userstats = proportions.PersonStats(userdata)

        traveldist = userstats.height

        soundtime = TV(traveldist / ONE_SOUNDSECOND)
        printtime = pretty_time_delta(soundtime, True, True)

        if is_SV:
            desc = f"To travel {traveldist:,.3mu}, it would take sound **{printtime}**."
        else:
            desc = f"To travel from **{userstats.nickname}**'s head to their {engine.plural(userstats.footname).lower()}, it would take sound **{printtime}**."

        embedtosend = discord.Embed(title = f"Sound Travel Time in {traveldist:,.3mu}",
                                    description = desc)

        await ctx.send(embed = embedtosend)

    @commands.command(
        usage = "<user or length>",
        category = "stats"
    )
    async def light(self, ctx, *, who: MemberOrSize = None):
        """Find how long it would take light to travel a length or height."""
        ONE_LIGHTSECOND = SV(299792000)
        is_SV = False

        if who is None:
            who = ctx.message.author

        if isinstance(who, SV):
            is_SV = True

        userdata = load_or_fake(who)
        userstats = proportions.PersonStats(userdata)

        traveldist = userstats.height

        lighttime = TV(traveldist / ONE_LIGHTSECOND)
        printtime = pretty_time_delta(lighttime, True, True)

        if is_SV:
            desc = f"To travel {traveldist:,.3mu}, it would take light **{printtime}**."
        else:
            desc = f"To travel from **{userstats.nickname}**'s head to their {engine.plural(userstats.footname).lower()}, it would take light **{printtime}**."

        embedtosend = discord.Embed(title = f"Light Travel Time in {traveldist:,.3mu}",
                                    description = desc)

        await ctx.send(embed = embedtosend)

    @commands.command(
        usage = "<distance>"
    )
    async def fall(self, ctx, distance: MemberOrSize):
        if isinstance(distance, discord.Member):
            ud = userdb.load(ctx.guild.id, distance.id)
            distance = ud.height
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        basemass = userdata.baseweight
        scale = userdata.scale
        time, vm, fl = freefall(basemass, distance, scale)
        ftime = pretty_time_delta(time, millisecondAccuracy = True, roundeventually = True)

        await ctx.send(f"You fell **{distance:,.3mu}** in **{ftime}**!\n"
                       f"𝑉𝑚𝑎𝑥: {vm:.3m}/s [That feels like falling **{fl:,.3mu}**!]")

    @commands.command(
        usage = "<distance>",
        hidden = True
    )
    async def rpfall(self, ctx, distance: MemberOrSize):
        if isinstance(distance, discord.Member):
            ud = userdb.load(ctx.guild.id, distance.id)
            distance = ud.height
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        basemass = userdata.baseweight
        scale = 1
        fakedistance = SV(distance / userdata.scale)
        time, vm, fl = freefall(basemass, distance, scale)
        ftime = pretty_time_delta(time, millisecondAccuracy = True, roundeventually = True)

        await ctx.send(f"You fell **{fakedistance:,.3mu}** in **{ftime}**!\n"
                       f"𝑉𝑚𝑎𝑥: {vm:.3m}/s [That feels like falling **{fl:,.3mu}**!]")

    @commands.command(
        aliases = [],
        usage = "<users...>",
        category = "stats"
    )
    @commands.guild_only()
    async def lineup(self, ctx):
        """Lineup a bunch of people for comparison."""
        if not ctx.message.mentions:
            await ctx.send("At least one person is required")
            return

        failedusers = []
        userdatas = []
        for member in ctx.message.mentions:
            try:
                userdatas.append(userdb.load(member.guild.id, member.id, member=member))
            except errors.UserNotFoundException:
                failedusers.append(member)

        # TODO: Raise exception instead
        # Later Digi asks: why? This is fine?
        if failedusers:
            nicks = sentence_join((u.display_name for u in failedusers), oxford=True)
            if len(failedusers) == 1:
                failmessage = f"{nicks} is not a SizeBot user."
            else:
                failmessage = f"{nicks} are not SizeBot users."
            await ctx.send(failmessage)
            return

        msg = await ctx.send(emojis.loading + " *Loading comparison...*")

        users = [{"name": u.nickname, "model": u.macrovision_model, "view": u.macrovision_view, "height": u.height} for u in userdatas]

        nicks = sentence_join((u.nickname for u in userdatas), oxford=True)
        e = discord.Embed(
            title="Click here for lineup image!",
            description=f"Lineup of {nicks}",
            color=colors.cyan,
            url = await macrovision.get_url(users)
        )
        await msg.edit(content = "", embed = e)

    @commands.command(
        aliases = ["simplecomp", "simplecomparison"],
        usage = "<user/height> [user/height]",
        category = "stats"
    )
    @commands.guild_only()
    async def simplecompare(self, ctx, memberOrHeight: MemberOrSize = None,
                            *, memberOrHeight2: MemberOrSize = None):
        """Compare two users' size.

        If give one user, compares you to that user."""
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.author

        if memberOrHeight is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.")
            return

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight).save()
        if isinstance(memberOrHeight2, SV):
            telemetry.SizeViewed(memberOrHeight).save()

        userdata1 = load_or_fake(memberOrHeight)
        userdata2 = load_or_fake(memberOrHeight2)

        msg = await ctx.send(emojis.loading + " *Loading comparison...*")

        comparison = proportions.PersonComparison(userdata1, userdata2)
        e = await comparison.toSimpleEmbed(ctx.author.id)
        await msg.edit(content = "", embed = e)

    @commands.command(
        aliases = ["minecraft", "scopic"],
        usage = "[user]",
        category = "stats"
    )
    async def pehkui(self, ctx, *, who: MemberOrSize = None):
        """Get your (or a user's) Pehkui scale.

        For use in the Pehkui Minecraft mod. Essentially a height represented in a unit of Steves."""

        if who is None:
            who = ctx.message.author

        userdata = load_or_fake(who)
        userstats = proportions.PersonStats(userdata)

        if userdata.height == 0:
            await ctx.send(f"{userdata.nickname} doesn't exist...")
            return

        STEVE = SV(1.8)
        user_pehkui = Decimal(userstats.height / STEVE)

        await ctx.send(f"{userdata.nickname}'s Pehkui scale is **{user_pehkui:.6}**.")

    @commands.command(
        aliases = ["g", "gravity"],
        usage = "<user> [user]",
        category = "stats"
    )
    async def gravitycompare(self, ctx, memberOrHeight: MemberOrSize = None,
                             *, memberOrHeight2: MemberOrSize = None):
        """
        Compare two users' gravitation pull.
        """
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.author

        if memberOrHeight is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.")
            return

        if isinstance(memberOrHeight, SV):
            telemetry.SizeViewed(memberOrHeight).save()
        if isinstance(memberOrHeight2, SV):
            telemetry.SizeViewed(memberOrHeight).save()

        userdata1 = load_or_fake(memberOrHeight)
        userdata2 = load_or_fake(memberOrHeight2)
        larger_person, smaller_person = (userdata1, userdata2) if userdata1.height > userdata2.height else (userdata2, userdata1)

        # RP rules
        larger_person.scale = larger_person.scale / smaller_person.scale
        smaller_person.scale = 1

        r = SV(larger_person.height * 4)
        G = Decimal(6.673 * (10**-11))
        f = (G * (larger_person.weight / 1000) * (smaller_person.weight / 1000)) / (r**2)
        gs = (Decimal(9.81) * f) / (smaller_person.weight / 1000)

        await ctx.send(f"Standing on {larger_person.nickname}, {smaller_person.nickname} would experience **{gs:.3}**g of gravitational force.")


async def setup(bot):
    await bot.add_cog(StatsCog(bot))
