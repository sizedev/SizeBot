import os
import sys
import traceback
from decimal import Decimal, InvalidOperation

import discord
from discord.ext import commands

# TODO: Fix this...
from globalsb import NICK, DISP, CHEI, BHEI, BWEI, DENS, UNIT, SPEC
from globalsb import read_user, folder, getnum, getlet, isFeetAndInchesAndIfSoFixIt, place_value
from globalsb import defaultheight, defaultweight, defaultdensity, inch
from globalsb import fromSVacc, fromSVUSA, fromSV, fromWV, fromWVUSA, toShoeSize, toSV


# TODO: Move to logging module
# Error debugging
async def print_error(ctx, error):
    print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
    await ctx.send(f"Error? {error}")


# TODO: Move to units module
# Conversion constants
footfactor = Decimal(1) / Decimal(7)
footwidthfactor = footfactor / Decimal(2.5)
footthickfactor = Decimal(1) / Decimal(65)
thumbfactor = Decimal(1) / Decimal(26)
fingerprintfactor = Decimal(1) / Decimal(35080)
hairwidthfactor = Decimal(1) / Decimal(23387)


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def stats(self, ctx, who: discord.Member = None):
        if who is None:
            who = ctx.message.author

        whoid = str(who.id)
        if not os.path.exists(folder + "/users/" + whoid + ".txt"):
            # User file missing
            await ctx.send(
                "Sorry! User isn't registered with SizeBot.\n"
                "To register, use the `&register` command.",
                delete_after=5)
            return

        user1 = read_user(whoid)
        readableheight = fromSVacc(user1[CHEI])
        readablefootheight = fromSVacc(Decimal(user1[CHEI]) * footfactor)
        readablefootUSAheight = fromSVUSA(Decimal(user1[CHEI]) * footfactor)
        readablefootthick = fromSVacc(Decimal(user1[CHEI]) * footthickfactor)
        readablefootUSAthick = fromSVUSA(Decimal(user1[CHEI]) * footthickfactor)
        readableUSAheight = fromSVUSA(user1[CHEI])
        userbaseh = fromSV(user1[BHEI])
        userbasehusa = fromSVUSA(user1[BHEI])
        userbasew = fromWV(user1[BWEI])
        userbasewusa = fromWVUSA(user1[BWEI])
        density = Decimal(user1[DENS])
        multiplier = Decimal(user1[CHEI]) / Decimal(user1[BHEI])
        basemult = Decimal(user1[CHEI]) / Decimal(defaultheight)
        multipliercubed = multiplier**3
        basemultcubed = basemult**3
        baseweight = Decimal(user1[BWEI])
        weightmath = (baseweight * (multipliercubed)) * density
        readableweight = fromWV(weightmath)
        readableUSAweight = fromWVUSA(weightmath)
        normalheight = fromSVacc(Decimal(defaultheight) / Decimal(basemult))
        normalUSAheight = fromSVUSA(Decimal(defaultheight) / Decimal(basemult))
        normalweight = fromWV(Decimal(defaultweight) / Decimal(basemultcubed))
        normalUSAweight = fromWVUSA(Decimal(defaultweight) / Decimal(basemultcubed))
        thumbsize = fromSVacc(Decimal(user1[CHEI]) * thumbfactor)
        thumbsizeUSA = fromSVUSA(Decimal(user1[CHEI]) * thumbfactor)
        footheight = Decimal(user1[CHEI]) * footfactor
        footwidth = fromSV(Decimal(user1[CHEI]) * footwidthfactor)
        footwidthUSA = fromSVUSA(Decimal(user1[CHEI]) * footwidthfactor)
        footlengthinches = Decimal(user1[CHEI]) * footfactor / inch
        footlengthinches = round(footlengthinches, 3)
        shoesize = toShoeSize(footlengthinches)
        fingerprintdepth = fromSVacc(Decimal(user1[CHEI]) * fingerprintfactor)
        fingerprintdepthUSA = fromSVUSA(Decimal(user1[CHEI]) * fingerprintfactor)
        hairwidth = fromSVacc(Decimal(user1[CHEI]) * hairwidthfactor)
        hairwidthUSA = fromSVUSA(Decimal(user1[CHEI]) * hairwidthfactor)
        hcms = place_value(round(multiplier, 3))
        hbms = place_value(round(basemult, 3))
        wcms = place_value(round(multipliercubed * density, 3))
        wbms = place_value(round(basemultcubed * density, 3))
        if multiplier > 999999999999999:
            hcms = "{:.2e}".format(multiplier)
        if basemult > 999999999999999:
            hbms = "{:.2e}".format(basemult)
        if multipliercubed > 999999999999999:
            wcms = "{:.2e}".format(multipliercubed * density)
        if basemultcubed > 999999999999999:
            wbms = "{:.2e}".format(basemultcubed * density)

        await ctx.send(
            f"**<@{whoid}> Stats:**\n"
            f"Current Height: {readableheight} | {readableUSAheight} ({hcms}x character base, {hbms}x normal)\n"
            f"Current Weight: {readableweight} | {readableUSAweight} ({wcms}x charbase, {wbms}x norm)\n"
            f"Current Density: {density}x\n"
            f"Foot Length: {readablefootheight} | {readablefootUSAheight} ({shoesize})\n"
            f"Foot Width: {footwidth} | {footwidthUSA}\n"
            f"Toe Height: {readablefootthick} | {readablefootUSAthick}\n"
            f"Thumb Size: {thumbsize} | {thumbsizeUSA}\n"
            f"Fingerprint Depth: {fingerprintdepth} | {fingerprintdepthUSA}\n"
            f"Hair Width: {hairwidth} | {hairwidthUSA}\n"
            f"Size of a Normal Man (Comparative) {normalheight} | {normalUSAheight}\n"
            f"Weight of a Normal Man (Comparative) {normalweight} | {normalUSAweight}\n"
            f"Character Bases: {userbaseh}, {userbasehusa} | {userbasew}, {userbasewusa}")
        print(f"Stats for {user1} sent.")
        pass

    @commands.command()
    async def statsraw(self, ctx, heightstring: str = None):
        if heightstring is None:
            heightstring = "5.5ft"

        heightstring = isFeetAndInchesAndIfSoFixIt(heightstring)

        height = toSV(getnum(heightstring), getlet(heightstring))
        userarray = [
            "Raw\n",
            "Y\n",
            height,
            defaultheight,
            defaultweight,
            defaultdensity,
            "M\n",
            "None\n"
        ]
        readableheight = fromSVacc(userarray[CHEI])
        readablefootheight = fromSVacc(Decimal(userarray[CHEI]) * footfactor)
        readablefootUSAheight = fromSVUSA(Decimal(userarray[CHEI]) * footfactor)
        readablefootthick = fromSVacc(Decimal(userarray[CHEI]) * footthickfactor)
        readablefootUSAthick = fromSVUSA(Decimal(userarray[CHEI]) * footthickfactor)
        readableUSAheight = fromSVUSA(userarray[CHEI])
        userbaseh = fromSV(userarray[BHEI])
        userbasehusa = fromSVUSA(userarray[BHEI])
        userbasew = fromWV(userarray[BWEI])
        userbasewusa = fromWVUSA(userarray[BWEI])
        density = Decimal(userarray[DENS])
        multiplier = Decimal(userarray[CHEI]) / Decimal(userarray[BHEI])
        basemult = Decimal(userarray[CHEI]) / Decimal(defaultheight)
        multipliercubed = multiplier**3
        basemultcubed = basemult**3
        baseweight = Decimal(userarray[BWEI])
        weightmath = (baseweight * (multipliercubed)) * density
        readableweight = fromWV(weightmath)
        readableUSAweight = fromWVUSA(weightmath)
        normalheight = fromSVacc(Decimal(defaultheight) / Decimal(basemult))
        normalUSAheight = fromSVUSA(Decimal(defaultheight) / Decimal(basemult))
        normalweight = fromWV(Decimal(defaultweight) / Decimal(basemultcubed))
        normalUSAweight = fromWVUSA(Decimal(defaultweight) / Decimal(basemultcubed))
        thumbsize = fromSVacc(Decimal(userarray[CHEI]) * thumbfactor)
        thumbsizeUSA = fromSVUSA(Decimal(userarray[CHEI]) * thumbfactor)
        footheight = Decimal(userarray[CHEI]) * footfactor
        footwidth = fromSV(Decimal(userarray[CHEI]) * footwidthfactor)
        footwidthUSA = fromSVUSA(Decimal(userarray[CHEI]) * footwidthfactor)
        footlengthinches = Decimal(userarray[CHEI]) * footfactor / inch
        shoesize = toShoeSize(footlengthinches)
        fingerprintdepth = fromSVacc(Decimal(userarray[CHEI]) * fingerprintfactor)
        fingerprintdepthUSA = fromSVUSA(Decimal(userarray[CHEI]) * fingerprintfactor)
        hairwidth = fromSVacc(Decimal(userarray[CHEI]) * hairwidthfactor)
        hairwidthUSA = fromSVUSA(Decimal(userarray[CHEI]) * hairwidthfactor)
        hcms = place_value(round(multiplier, 3))
        hbms = place_value(round(basemult, 3))
        wcms = place_value(round(multipliercubed * density, 3))
        wbms = place_value(round(basemultcubed * density, 3))
        if multiplier > 999999999999999:
            hcms = "{:.2e}".format(multiplier)
        if basemult > 999999999999999:
            hbms = "{:.2e}".format(basemult)
        if multipliercubed > 999999999999999:
            wcms = "{:.2e}".format(multipliercubed * density)
        if basemultcubed > 999999999999999:
            wbms = "{:.2e}".format(basemultcubed * density)

        await ctx.send(
            f"**{heightstring} Stats:**\n"
            f"Current Height: {readableheight} | {readableUSAheight} ({hbms}x normal)\n"
            f"Current Weight: {readableweight} | {readableUSAweight} ({wbms}x normal)\n"
            f"Foot Length: {readablefootheight} | {readablefootUSAheight} ({shoesize})\n"
            f"Foot Width: {footwidth} | {footwidthUSA}\n"
            f"Toe Height: {readablefootthick} | {readablefootUSAthick}\n"
            f"Thumb Size: {thumbsize} | {thumbsizeUSA}\n"
            f"Fingerprint Depth: {fingerprintdepth} | {fingerprintdepthUSA}\n"
            f"Hair Width: {hairwidth} | {hairwidthUSA}\n"
            f"Size of a Normal Man (Comparative) {normalheight} | {normalUSAheight}\n"
            f"Weight of a Normal Man (Comparative) {normalweight} | {normalUSAweight}")
        print(f"Stats for {heightstring} sent.")
        pass

    @commands.command()
    async def compare(self, ctx, user1: discord.Member = None, user2: discord.Member = None):
        if user2 is None:
            user2 = ctx.message.author

        if user1 is None:
            await ctx.send("Please use either two parameters to compare two people, or one to compare with yourself.", delete_after=5)
            return

        user1id = str(user1.id)
        user2id = str(user2.id)
        user1tag = f"<@{user1id}>"
        user2tag = f"<@{user2id}>"

        if not os.path.exists(folder + "/users/" + user1id + ".txt") or not os.path.exists(folder + "/users/" + user2id + ".txt"):
            # User file missing
            await ctx.send(
                "Sorry! User isn't registered with SizeBot.\n"
                "To register, use the `& register` command.",
                delete_after=5)
            return

        user1 = read_user(user1id)
        user2 = read_user(user2id)

        output = self.compare_users(user1tag, user1, user2tag, user2)
        await ctx.send(output)
        print(f"Compared {user1} and {user2}")

    @commands.command()
    async def compareraw(self, ctx, height: str = None, user1: discord.Member = None):
        if height is None:
            height = "5.5ft"

        height = isFeetAndInchesAndIfSoFixIt(height)
        height = toSV(getnum(height), getlet(height))

        if user1 is None:
            user1id = str(ctx.message.author.id)
        else:
            user1id = str(user1.id)

        user1tag = f"<@{user1id}>"
        user2tag = f"**Raw**"

        if not os.path.exists(folder + "/users/" + user1id + ".txt"):
            # User file missing
            await ctx.send(
                "Sorry! User isn't registered with SizeBot.\n"
                "To register, use the `& register` command.",
                delete_after=5)
            return

        user1 = read_user(ctx.message.author.id)
        # TODO: Check if user is registered
        user2 = [
            "Raw\n",
            "Y\n",
            height,
            defaultheight,
            defaultweight,
            defaultdensity,
            "M\n",
            "None\n"
        ]

        output = self.compare_users(user1tag, user1, user2tag, user2)
        await ctx.send(output)
        print(f"Compared {ctx.message.author.name} and {height}")

    def compare_users(self, user1tag, user1, user2tag, user2):
        if Decimal(user1[CHEI]) == Decimal(user2[CHEI]):
            return f"{user1tag} and {user2tag} match 1 to 1."

        if Decimal(user1[CHEI]) > Decimal(user2[CHEI]):
            biguser = user1
            bigusertag = user1tag
            smalluser = user2
            smallusertag = user2tag
        else:
            biguser = user2
            bigusertag = user2tag
            smalluser = user1
            smallusertag = user1tag

        # Compare
        bch = Decimal(biguser[CHEI])
        bbh = Decimal(biguser[BHEI])
        sch = Decimal(smalluser[CHEI])
        sbh = Decimal(smalluser[BHEI])
        bbw = Decimal(biguser[BWEI])
        sbw = Decimal(smalluser[BWEI])
        bd = Decimal(biguser[DENS])
        sd = Decimal(smalluser[DENS])
        bigmult = bch / bbh
        smallmult = sch / sbh
        bcw = bbw * (bigmult ** 3) * bd
        scw = sbw * (smallmult ** 3) * sd
        diffmult = bigmult / smallmult
        b2sh = bbh * diffmult
        s2bh = sbh / diffmult
        b2sw = bbw * (diffmult ** 3)
        s2bw = sbw / (diffmult ** 3)
        bigtosmallheight = fromSVacc(b2sh)
        smalltobigheight = fromSVacc(s2bh)
        bigtosmallheightUSA = fromSVUSA(b2sh)
        smalltobigheightUSA = fromSVUSA(s2bh)
        bigtosmallfoot = fromSVacc(b2sh / 7)
        smalltobigfoot = fromSVacc(s2bh / 7)
        bigtosmallfootUSA = fromSVUSA(b2sh / 7)
        smalltobigfootUSA = fromSVUSA(s2bh / 7)
        bigtosmallshoe = toShoeSize(b2sh / 7 / inch)
        smalltobigshoe = toShoeSize(s2bh / 7 / inch)
        bigtosmallweight = fromWV(b2sw)
        smalltobigweight = fromWV(s2bw)
        bigtosmallweightUSA = fromWVUSA(b2sw)
        smalltobigweightUSA = fromWVUSA(s2bw)
        timestaller = place_value(round((bch / sch), 3))

        # Print compare
        return (
            "**Comparison:**\n"
            f"{bigusertag} is really: {fromSVacc(bch)} / {fromSVUSA(bch)} | {fromWV(bcw)} / {fromWVUSA(bcw)}.\n"
            f"To {smallusertag}, {bigusertag} looks: {bigtosmallheight} / {bigtosmallheightUSA} | {bigtosmallweight} / {bigtosmallweightUSA}.\n"
            f"To {smallusertag}, {bigusertag}'s foot looks: {bigtosmallfoot} / {bigtosmallfootUSA} long. ({bigtosmallshoe})\n"
            "\n"
            f"{bigusertag} is {timestaller}x taller than {smallusertag}.\n"
            "\n"
            f"{smallusertag} is really: {fromSVacc(sch)} / {fromSVUSA(sch)} | {fromWV(scw)} / {fromWVUSA(scw)}\n"
            f"To {bigusertag}, {smallusertag} looks: {smalltobigheight} / {smalltobigheightUSA} | {smalltobigweight} / {smalltobigweightUSA}.\n"
            f"To {bigusertag}, {smallusertag}'s foot looks: {smalltobigfoot} / {smalltobigfootUSA} long. ({smalltobigshoe})")

    @stats.error
    async def stats_handler(self, ctx, error):
        if isinstance(error, InvalidOperation):
            await ctx.send(
                "SizeBot cannot perform this action due to a math error.\n"
                f"Are you too big, {ctx.message.author.id}?")
        print_error(ctx.command, error)

    @statsraw.error
    async def statsraw_handler(self, ctx, error):
        if isinstance(error, InvalidOperation):
            await ctx.send(
                "SizeBot cannot perform this action due to a math error.\n"
                f"Are you too big, {ctx.message.author.id}?")
        print_error(ctx.command, error)

    @compare.error
    async def compare_handler(self, ctx, error):
        print_error(ctx.command, error)

    @compareraw.error
    async def compareraw_handler(self, ctx, error):
        print_error(ctx.command, error)


# Necessary
def setup(bot):
    bot.add_cog(StatsCog(bot))
