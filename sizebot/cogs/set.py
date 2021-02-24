import logging
import re

import discord
from discord.ext import commands

from sizebot.cogs.register import showNextStep
from sizebot.lib import decimal, errors, userdb, nickmanager
from sizebot.lib.decimal import Decimal
from sizebot.lib.diff import Diff
from sizebot.lib.diff import Rate as ParseableRate
from sizebot.lib.proportions import formatShoeSize, fromShoeSize
from sizebot.lib.units import SV, WV
from sizebot.lib.utils import AliasMap, glitch_string

logger = logging.getLogger("sizebot")


class SetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases = ["changenick", "nick"],
        usage = "<nick>",
        category = "set"
    )
    @commands.guild_only()
    async def setnick(self, ctx, *, newnick):
        """Change nickname."""
        # TODO: Disable and hide this command on servers where bot does not have MANAGE_NICKNAMES permission
        # TODO: If the bot has MANAGE_NICKNAMES permission but can't change this user's permission, let the user know
        # TODO: If the bot has MANAGE_NICKNAMES permission but can't change this user's permission, and the user is an admin, let them know they may need to fix permissions
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.nickname = newnick
        userdb.save(userdata)

        await ctx.send(f"<@{ctx.author.id}>'s nick is now {userdata.nickname}")

        await nickmanager.nick_update(ctx.author)
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<species>",
        category = "set"
    )
    @commands.guild_only()
    async def setspecies(self, ctx, *, newtag):
        """Change species."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.species = newtag
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s species is now a {userdata.species}.")

        await nickmanager.nick_update(ctx.author)
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["clearspecies"],
        category = "set"
    )
    @commands.guild_only()
    async def resetspecies(self, ctx):
        """Remove species."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.species = None
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s species is now cleared.")

        await nickmanager.nick_update(ctx.author)
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<Y/N>",
        category = "set"
    )
    @commands.guild_only()
    async def setdisplay(self, ctx, newdisp: bool):
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
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<M/U>",
        category = "set"
    )
    @commands.guild_only()
    async def setsystem(self, ctx, newsys):
        """Set measurement system."""
        newsys = newsys.lower()
        systemmap = AliasMap({
            "m": ("b", "e", "metric", "british", "europe", "european"),
            "u": ("i", "c", "a", "us", "imperial", "customary", "american")
        })

        if newsys not in systemmap:
            await ctx.send(f"Please enter `{ctx.prefix}{ctx.invoked_with} {ctx.command.usage}`.")
            return

        newsys = systemmap[newsys]

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.unitsystem = newsys
        completed_registration = userdata.complete_step("setsystem")
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s system is now set to {userdata.unitsystem}.")

        await nickmanager.nick_update(ctx.author)
        await showNextStep(ctx, userdata, completed=completed_registration)

    @commands.command(
        aliases = ["setsize"],
        usage = "<height>",
        category = "set"
    )
    @commands.guild_only()
    async def setheight(self, ctx, *, newheight: SV):
        """Change height."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.height = newheight
        completed_registration = userdata.complete_step("setheight")
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname} is now {userdata.height:mu} tall.")

        await nickmanager.nick_update(ctx.author)
        await showNextStep(ctx, userdata, completed=completed_registration)

    @commands.command(
        usage = "<scale>",
        category = "set"
    )
    @commands.guild_only()
    async def setscale(self, ctx, *, newscale):
        """Change height by scale."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        if newscale == "<:116:793260849007296522>":
            scale = Decimal("1/16")
        elif newscale == "<:1144:793260894686806026>" or newscale == "<:1122:793262146917105664>":
            scale = Decimal("1/144")
        else:
            re_scale = r"(\d+\.?\d*)[:/]?(\d+\.?\d*)?"
            if m := re.match(re_scale, newscale):
                multiplier = m.group(1)
                factor = m.group(2) if m.group(2) else 1
            else:
                raise errors.UserMessedUpException(f"{newscale} is not a valid scale factor.")

            scale = Decimal(multiplier) / Decimal(factor)

        userdata.height = userdata.baseheight * scale
        completed_registration = userdata.complete_step("setheight")
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname} is now {userdata.height:mu} tall.")

        await nickmanager.nick_update(ctx.author)
        await showNextStep(ctx, userdata, completed=completed_registration)

    @commands.command(
        aliases = ["copysize"],
        usage = "<user> [factor]",
        category = "set"
    )
    @commands.guild_only()
    async def copyheight(self, ctx, user: discord.Member, *, newscale):
        """Be the size of another user, modified by a factor."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        otheruser = userdb.load(ctx.guild.id, user.id)

        userdata.height = otheruser.height

        if newscale == "<:116:793260849007296522>":
            scale = Decimal("1/16")
        elif newscale == "<:1144:793260894686806026>" or newscale == "<:1122:793262146917105664>":
            scale = Decimal("1/144")
        else:
            re_scale = r"(\d+\.?\d*)[:/]?(\d+\.?\d*)?"
            if m := re.match(re_scale, newscale):
                multiplier = m.group(1)
                factor = m.group(2) if m.group(2) else 1
            else:
                raise errors.UserMessedUpException(f"{newscale} is not a valid scale factor.")

            scale = Decimal(multiplier) / Decimal(factor)

        userdata.height = userdata.height * scale
        completed_registration = userdata.complete_step("setheight")
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname} is now {userdata.height:mu} tall.")

        await nickmanager.nick_update(ctx.author)
        await showNextStep(ctx, userdata, completed=completed_registration)

    @commands.command(
        aliases = ["resetsize", "reset", "resetscale"],
        category = "set"
    )
    @commands.guild_only()
    async def resetheight(self, ctx):
        """Reset height/size."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.height = userdata.baseheight
        userdb.save(userdata)

        await ctx.send(f"{ctx.author.display_name} reset their size.")

        await nickmanager.nick_update(ctx.author)
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["setrandomsize"],
        usage = "<minheight> <maxheight>",
        category = "set"
    )
    @commands.guild_only()
    async def setrandomheight(self, ctx, minheight: SV, maxheight: SV):
        """Change height to a random value.

        Sets your height to a height between `minheight` and `maxheight`.
        Weighted on a logarithmic curve."""
        if minheight < 0:
            minheight = SV(0)
        if maxheight < 0:
            maxheight = SV(0)

        newheightSV = decimal.randRangeLog(minheight, maxheight)

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.height = newheightSV
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname} is now {userdata.height:mu} tall.")

        await nickmanager.nick_update(ctx.author)
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["inf"],
        category = "set"
    )
    @commands.guild_only()
    async def setinf(self, ctx):
        """Change height to infinity."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.height = SV("infinity")
        completed_registration = userdata.complete_step("setheight")
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname} is now infinitely tall.")

        await nickmanager.nick_update(ctx.author)
        await showNextStep(ctx, userdata, completed=completed_registration)

    @commands.command(
        aliases = ["0"],
        category = "set"
    )
    @commands.guild_only()
    async def set0(self, ctx):
        """Change height to a zero."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.height = 0
        completed_registration = userdata.complete_step("setheight")
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname} is now nothing.")

        await nickmanager.nick_update(ctx.author)
        await showNextStep(ctx, userdata, completed=completed_registration)

    @commands.command(
        usage = "<weight>",
        category = "set"
    )
    async def setweight(self, ctx, *, newweight: WV):
        """Set your current weight."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.weight = newweight
        completed_registration = userdata.complete_step("setweight")
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s weight is now {userdata.weight:mu}")

        await nickmanager.nick_update(ctx.author)
        await showNextStep(ctx, userdata, completed=completed_registration)

    @commands.command(
        usage = "<foot>",
        category = "set"
    )
    async def setfoot(self, ctx, *, newfoot):
        """Set your current foot length."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.footlength = SV(SV.parse(newfoot) * userdata.viewscale)
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s base foot length is now {userdata.footlength:mu} long ({formatShoeSize(userdata.footlength)}), "
                       f"or {(SV(userdata.footlength * userdata.scale)):mu} currently. {formatShoeSize(SV(userdata.footlength * userdata.scale))}")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["setshoesize"],
        usage = "<shoe>",
        category = "set"
    )
    async def setshoe(self, ctx, *, newshoe):
        """Set your current shoe size.

        Accepts a US Shoe Size.
        If a W is in the shoe size anywhere, it is parsed as a Women's size.
        If a C is in the show size anywhere, it is parsed as a Children's size."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        newfoot = fromShoeSize(newshoe)

        userdata.footlength = SV(newfoot * userdata.viewscale)
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s base foot length is now {userdata.footlength:mu} long ({formatShoeSize(userdata.footlength)}), "
                       f"or {(SV(userdata.footlength * userdata.scale)):mu} currently. {formatShoeSize(SV(userdata.footlength * userdata.scale))}")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["clearfoot", "unsetfoot"],
        category = "set"
    )
    @commands.guild_only()
    async def resetfoot(self, ctx):
        """Remove custom foot length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.footlength = None
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s foot length is now default.")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["pawtoggle"],
        category = "set"
    )
    @commands.guild_only()
    async def togglepaw(self, ctx):
        """Switch between the word "foot" and "paw" for your stats."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.pawtoggle = not userdata.pawtoggle
        userdb.save(userdata)

        await ctx.send(f"The end of {userdata.nickname}'s legs are now called a {userdata.footname.lower()}.")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["furtoggle"],
        category = "set"
    )
    @commands.guild_only()
    async def togglefur(self, ctx):
        """Switch between the word "hair" and "fur" for your stats."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.furtoggle = not userdata.furtoggle
        userdb.save(userdata)

        await ctx.send(f"The hair of {userdata.nickname} is now called {userdata.hairname.lower()}.")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["incomprehensibletoggle", "toggleincomp", "incomptoggle"],
        category = "set"
    )
    @commands.guild_only()
    async def toggleincomprehensible(self, ctx):
        """You stare into the void."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.incomprehensible = not userdata.incomprehensible
        userdb.save(userdata)

        out_str = f"{userdata.nickname} is now understandable by mortals."

        if userdata.incomprehensible:
            out_str = f"{userdata.nickname} " + glitch_string(" i ain't the sharpest tool in the shed") + "."

        await ctx.send(out_str)
        await nickmanager.nick_update(ctx.author)
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<hair>",
        category = "set"
    )
    async def sethair(self, ctx, *, newhair):
        """Set your current hair length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        newhairsv = SV(SV.parse(newhair) * userdata.viewscale)

        userdata.hairlength = newhairsv
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s base hair length is now {userdata.hairlength:mu} long, "
                       f"or {SV(userdata.hairlength):mu} currently.")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<tail>",
        category = "set"
    )
    async def settail(self, ctx, *, newtail):
        """Set your current tail length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        newtailsv = SV(SV.parse(newtail) * userdata.viewscale)

        userdata.taillength = newtailsv
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s base tail length is now {userdata.taillength:mu} long, "
                       f"or {SV(userdata.taillength):mu} currently.")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["cleartail", "unsettail"],
        category = "set"
    )
    @commands.guild_only()
    async def resettail(self, ctx):
        """Remove custom tail length."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.taillength = None
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s tail length is now cleared.")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<ear>",
        category = "set"
    )
    async def setear(self, ctx, *, newear):
        """Set your current ear heightear."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        newearsv = SV(SV.parse(newear) * userdata.viewscale)

        userdata.earheight = newearsv
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s base ear height is now {userdata.earheight:mu} long, "
                       f"or {SV(userdata.earheight):mu} currently.")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["clearear", "unsetear"],
        category = "set"
    )
    @commands.guild_only()
    async def resetear(self, ctx):
        """Remove custom ear height."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.earheight = None
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s ear height is now cleared.")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<weight>",
        category = "set"
    )
    async def setstrength(self, ctx, *, newstrength):
        """Set your current lift/carry strength."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.liftstrength = WV(WV.parse(newstrength) * (userdata.viewscale ** 3))
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s base lift strength is now {userdata.liftstrength:mu} long, "
                       f"or {SV(userdata.liftstrength):mu} currently.")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["clearstrength", "unsetstrength"],
        category = "set"
    )
    @commands.guild_only()
    async def resetstrength(self, ctx):
        """Remove custom lift/carry strength."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.liftstrength = None
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s lift/carry strength is now cleared.")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "set"
    )
    async def setwalk(self, ctx, *, newwalk: ParseableRate):
        """Set your current walk speed."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.walkperhour = ParseableRate(f"{newwalk.diff.amount * userdata.viewscale}/{newwalk.time}",
                                             Diff(f"{newwalk.diff.amount * userdata.viewscale}", "add", newwalk.diff.amount * userdata.viewscale),
                                             newwalk.time)
        userdb.save(userdata)

        # TODO: Give ParsableRates a __mul__ so I can give the user their current speeds.
        await ctx.send(f"{userdata.nickname}'s base walk speed is now {userdata.walkperhour:mu} per hour.")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["clearwalk", "unsetwalk"],
        category = "set"
    )
    @commands.guild_only()
    async def resetwalk(self, ctx):
        """Remove custom walk speed."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.walkperhour = None
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s walk speed is now cleared.")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "set"
    )
    async def setrun(self, ctx, *, newrun: ParseableRate):
        """Set your current run speed."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.runperhour = ParseableRate(f"{newrun.diff.amount * userdata.viewscale}/{newrun.time}",
                                            Diff(f"{newrun.diff.amount * userdata.viewscale}", "add", newrun.diff.amount * userdata.viewscale),
                                            newrun.time)
        userdb.save(userdata)

        # TODO: Give ParsableRates a __mul__ so I can give the user their current speeds.
        await ctx.send(f"{userdata.nickname}'s base run speed is now {userdata.runperhour:mu} per hour.")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["clearrun", "unsetrun"],
        category = "set"
    )
    @commands.guild_only()
    async def resetrun(self, ctx):
        """Remove custom run speed."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.runperhour = None
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s run speed is now cleared.")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<length>",
        category = "set"
    )
    async def setswim(self, ctx, *, newswim: ParseableRate):
        """Set your current swim speed."""

        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.swimperhour = ParseableRate(f"{newswim.diff.amount * userdata.viewscale}/{newswim.time}",
                                            Diff(f"{newswim.diff.amount * userdata.viewscale}", "add", newswim.diff.amount * userdata.viewscale),
                                            newswim.time)
        userdb.save(userdata)

        # TODO: Give ParsableRates a __mul__ so I can give the user their current speeds.
        await ctx.send(f"{userdata.nickname}'s base swim speed is now {userdata.swimperhour:mu} per hour.")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["clearswim", "unsetswim"],
        category = "set"
    )
    @commands.guild_only()
    async def resetswim(self, ctx):
        """Remove custom swim speed."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)

        userdata.swimperhour = None
        userdb.save(userdata)

        await ctx.send(f"{userdata.nickname}'s swim speed is now cleared.")
        await showNextStep(ctx, userdata)

    @commands.command(
        usage = "<male/female/none>",
        category = "set"
    )
    @commands.guild_only()
    async def setgender(self, ctx, gender):
        """Set gender."""
        guild = ctx.guild
        user = ctx.author

        gendermap = AliasMap({
            "m": ("male", "man", "boy"),
            "f": ("female", "woman", "girl"),
            None: ("none", "x", "nb")
        })
        try:
            gender = gendermap[gender.lower()]
        except KeyError:
            raise errors.ArgumentException

        userdata = userdb.load(guild.id, user.id, allow_unreg=True)
        userdata.gender = gender
        userdb.save(userdata)

        await nickmanager.nick_update(user)

        await ctx.send(f"{userdata.nickname}'s gender is now set to {userdata.gender}.")
        await showNextStep(ctx, userdata)

    @commands.command(
        aliases = ["cleargender", "unsetgender"],
        category = "set"
    )
    @commands.guild_only()
    async def resetgender(self, ctx):
        """Reset gender."""
        guild = ctx.guild
        user = ctx.author

        userdata = userdb.load(guild.id, user.id, allow_unreg=True)
        userdata.gender = None
        userdb.save(userdata)

        await nickmanager.nick_update(user)

        await ctx.send(f"{userdata.nickname}'s gender is now reset.")
        await showNextStep(ctx, userdata)

    @commands.command(
        category = "mod",
        hidden = True
    )
    @commands.guild_only()
    @commands.is_owner()
    async def setmodel(self, ctx, user: discord.Member, *, model):
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
    async def clearmodel(self, ctx, *, user: discord.Member):
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
    async def setview(self, ctx, user: discord.Member, *, view):
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
    async def clearview(self, ctx, *, user: discord.Member):
        userdata = userdb.load(ctx.guild.id, user.id)
        userdata.macrovision_view = None
        userdb.save(userdata)
        await ctx.send(f"Cleared {userdata.nickname}'s view.")


def setup(bot):
    bot.add_cog(SetCog(bot))
