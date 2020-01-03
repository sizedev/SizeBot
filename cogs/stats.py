import os
from decimal import Decimal, InvalidOperation

import discord
from discord.ext import commands

# TODO: Fix this...
from globalsb import NICK, DISP, CHEI, BHEI, BWEI, DENS, UNIT, SPEC
from globalsb import read_user, folder, getnum, getlet, isFeetAndInchesAndIfSoFixIt, place_value
from globalsb import defaultheight, defaultweight, defaultdensity, inch
from globalsb import fromSVacc, fromSVUSA, fromSV, fromWV, fromWVUSA, toShoeSize, toSV
from globalsb import printtab

import digilogger as logger

# TODO: Move to units module.
# Conversion constants.
footfactor = Decimal(1) / Decimal(7)
footwidthfactor = footfactor / Decimal(2.5)
footthickfactor = Decimal(1) / Decimal(65)
thumbfactor = Decimal(1) / Decimal(69.06)
fingerprintfactor = Decimal(1) / Decimal(35080)
hairwidthfactor = Decimal(1) / Decimal(23387)
pointerfactor = Decimal(1) / Decimal(17.26)


# TODO: Move to dedicated module.
async def get_user(ctx, user_string, fakename=None):
    try:
        member = await commands.MemberConverter().convert(ctx, user_string)
    except commands.errors.BadArgument:
        member = None

    if fakename is None:
        fakename = "Raw"

    if member:
        usertag = f"<@{member.id}>"
        user = load_user(member.id)
        if user is None:
            await ctx.send(
                "Sorry! User isn't registered with SizeBot.\n"
                "To register, use the `&register` command.",
                delete_after=5)
            return None, None
    else:
        usertag = fakename
        heightstring = isFeetAndInchesAndIfSoFixIt(user_string)
        height = toSV(getnum(heightstring), getlet(heightstring))
        if height is None:
            await ctx.send(
                "Sorry! I didn't recognize that user or height.",
                delete_after=5)
            return None, None

        user = height_to_user(height, fakename)

    return usertag, user


def load_user(userid):
    userid = str(userid)
    if not os.path.exists(folder + "/users/" + userid + ".txt"):
        # User file missing
        return None
    user = read_user(userid)
    return user


def height_to_user(height, fakename=None):
    if fakename is None:
        fakename = "Raw\n"
    else:
        fakename = fakename + "\n"

    user = [
        fakename,
        "Y\n",
        height,
        defaultheight,
        defaultweight,
        defaultdensity,
        "M\n",
        "None\n"
    ]
    return user


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def stats(self, ctx, who: str = None):
        if who is None:
            who = str(ctx.message.author.id)

        user1tag, user1 = await get_user(ctx, who)
        if user1 is None:
            return

        output = self.user_stats(user1tag, user1)
        await ctx.send(output)
        logger.msg(f"Stats for {who} sent.")

    @commands.command()
    async def compare(self, ctx, who1=None, who2=None, who1name=None, who2name=None):
        if who2 is None:
            who2 = str(ctx.message.author.id)

        if who1 is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.", delete_after=5)
            return

        if who1name is None:
            who1name = "Raw 1"

        if who2name is None:
            who2name = "Raw 2"

        user1tag, user1 = await get_user(ctx, who1, who1name)
        if user1 is None:
            await ctx.send(f"{who1} is not a recognized user or size.")
            return
        user2tag, user2 = await get_user(ctx, who2, who2name)
        if user2 is None:
            await ctx.send(f"{who2} is not a recognized user or size.")
            return

        output = self.compare_users(user1tag, user1, user2tag, user2)
        await ctx.send(output)
        logger.msg(f"Compared {user1} and {user2}")

    def compare_users(self, user1tag, user1, user2tag, user2):
        if Decimal(user1[CHEI]) == Decimal(user2[CHEI]):
            return f"{user1tag} and {user2tag} match 1 to 1."

        # Who's taller?
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

        # Compare math.
        bch = Decimal(biguser[CHEI])
        bbh = Decimal(biguser[BHEI])
        sch = Decimal(smalluser[CHEI])
        sbh = Decimal(smalluser[BHEI])
        bbw = Decimal(biguser[BWEI])
        sbw = Decimal(smalluser[BWEI])
        bd = Decimal(biguser[DENS])
        sd = Decimal(smalluser[DENS])
        bigmult = (bch / bbh)
        smallmult = (sch / sbh)
        bigmultcubed = (bigmult ** 3)
        smallmultcubed = (smallmult ** 3)
        dispbigmult = round(bigmult, 4)
        dispsmallmult = round(smallmult, 4)
        dispbigmultcubed = round(bigmultcubed, 4)
        dispsmallmultcubed = round(smallmultcubed, 4)
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
        bigtosmallfoot = fromSVacc(b2sh * footfactor)
        smalltobigfoot = fromSVacc(s2bh * footfactor)
        bigtosmallfootUSA = fromSVUSA(b2sh * footfactor)
        smalltobigfootUSA = fromSVUSA(s2bh * footfactor)
        bigtosmallshoe = toShoeSize(b2sh * footfactor)
        smalltobigshoe = toShoeSize(s2bh * footfactor)
        bigtosmallweight = fromWV(b2sw)
        smalltobigweight = fromWV(s2bw)
        bigtosmallweightUSA = fromWVUSA(b2sw)
        smalltobigweightUSA = fromWVUSA(s2bw)
        bigtosmallfootwidth = fromSVacc(b2sh * footwidthfactor)
        smalltobigfootwidth = fromSVacc(s2bh * footwidthfactor)
        bigtosmallfootwidthUSA = fromSVUSA(b2sh * footwidthfactor)
        smalltobigfootwidthUSA = fromSVUSA(s2bh * footwidthfactor)
        bigtosmallfootthick = fromSVacc(b2sh * footthickfactor)
        smalltobigfootthick = fromSVacc(s2bh * footthickfactor)
        bigtosmallfootthickUSA = fromSVUSA(b2sh * footthickfactor)
        smalltobigfootthickUSA = fromSVUSA(s2bh * footthickfactor)
        bigtosmallthumb = fromSVacc(b2sh * thumbfactor)
        smalltobigthumb = fromSVacc(s2bh * thumbfactor)
        bigtosmallthumbUSA = fromSVUSA(b2sh * thumbfactor)
        smalltobigthumbUSA = fromSVUSA(s2bh * thumbfactor)
        bigtosmallfingerprint = fromSVacc(b2sh * fingerprintfactor)
        smalltobigfingerprint = fromSVacc(s2bh * fingerprintfactor)
        bigtosmallfingerprintUSA = fromSVUSA(b2sh * fingerprintfactor)
        smalltobigfingerprintUSA = fromSVUSA(s2bh * fingerprintfactor)
        bigtosmallhairwidth = fromSVacc(b2sh * hairwidthfactor)
        smalltobighairwidth = fromSVacc(s2bh * hairwidthfactor)
        bigtosmallhairwidthUSA = fromSVUSA(b2sh * hairwidthfactor)
        smalltobighairwidthUSA = fromSVUSA(s2bh * hairwidthfactor)
        bigtosmallpointer = fromSVacc(b2sh * pointerfactor)
        smalltobigpointer = fromSVacc(s2bh * pointerfactor)
        bigtosmallpointerUSA = fromSVUSA(b2sh * pointerfactor)
        smalltobigpointerUSA = fromSVUSA(s2bh * pointerfactor)
        timestaller = place_value(round((bch / sch), 3))

        # Print compare.
        return (
            "**Comparison:**\n"
            f"{bigusertag} is really:\n"
            f"{printtab}Real Height: {fromSVacc(bch)} / {fromSVUSA(bch)} ({place_value(dispbigmult)}x basesize)\n"
            f"{printtab}Real Weight: {fromWV(bcw)} / {fromWVUSA(bcw)}. ({place_value(dispbigmultcubed)}x basesize)\n"
            f"To {smallusertag}, {bigusertag} looks:\n"
            f"{printtab}Height: {bigtosmallheight} / {bigtosmallheightUSA}\n"
            f"{printtab}Weight: {bigtosmallweight} / {bigtosmallweightUSA}\n"
            f"{printtab}Foot Length: {bigtosmallfoot} / {bigtosmallfootUSA} ({bigtosmallshoe})\n"
            f"{printtab}Foot Width: {bigtosmallfootwidth} / {bigtosmallfootwidthUSA}\n"
            f"{printtab}Toe Height: {bigtosmallfootthick} / {bigtosmallfootthickUSA}\n"
            f"{printtab}Pointer Finger Length: {bigtosmallpointer} / {bigtosmallpointerUSA}\n"
            f"{printtab}Thumb Width: {bigtosmallthumb} / {bigtosmallthumbUSA}\n"
            f"{printtab}Fingerprint Depth: {bigtosmallfingerprint} / {bigtosmallfingerprintUSA}\n"
            f"{printtab}Hair Width: {bigtosmallhairwidth} / {bigtosmallhairwidthUSA}\n"
            "\n"
            f"{bigusertag} is {timestaller}x taller than {smallusertag}.\n"
            "\n"
            f"{smallusertag} is really:\n"
            f"{printtab}Real Height: {fromSVacc(sch)} / {fromSVUSA(sch)} ({place_value(dispsmallmult)}x basesize)\n"
            f"{printtab}Real Weight: {fromWV(scw)} / {fromWVUSA(scw)}. ({place_value(dispsmallmultcubed)}x basesize)\n"
            f"To {bigusertag}, {smallusertag} looks:\n"
            f"{printtab}Height: {smalltobigheight} / {smalltobigheightUSA}\n"
            f"{printtab}Weight: {smalltobigweight} / {smalltobigweightUSA}\n"
            f"{printtab}Foot Length: {smalltobigfoot} / {smalltobigfootUSA} ({smalltobigshoe})\n"
            f"{printtab}Foot Width: {smalltobigfootwidth} / {smalltobigfootwidthUSA}\n"
            f"{printtab}Toe Height: {smalltobigfootthick} / {smalltobigfootthickUSA}\n"
            f"{printtab}Pointer Finger Length: {smalltobigpointer} / {smalltobigpointerUSA}\n"
            f"{printtab}Thumb Width: {smalltobigthumb} / {smalltobigthumbUSA}\n"
            f"{printtab}Fingerprint Depth: {smalltobigfingerprint} / {smalltobigfingerprintUSA}\n"
            f"{printtab}Hair Width: {smalltobighairwidth} / {smalltobighairwidthUSA}\n"
            "\n"
            f"**Base Sizes:**\n"
            f"{printtab}{bigusertag}: {fromSVacc(bbh)} / {fromSVUSA(bbh)} | {fromWV(bbw)} / {fromWVUSA(bbw)}\n"
            f"{printtab}{smallusertag}: {fromSVacc(sbh)} / {fromSVUSA(sbh)} | {fromWV(sbw)} / {fromWVUSA(sbw)}")

    def user_stats(self, usertag, user1):
        currentheight = Decimal(user1[CHEI])
        currentheight_m = fromSVacc(currentheight)
        currentheight_u = fromSVUSA(currentheight)

        baseheight = Decimal(user1[BHEI])
        baseheight_m = fromSVUSA(baseheight)
        baseheight_u = fromSV(baseheight)

        baseweight = Decimal(user1[BWEI])
        baseweight_m = fromWV(baseweight)
        baseweight_u = fromWVUSA(baseweight)

        density = Decimal(user1[DENS])

        multiplier = currentheight / baseheight
        defmultiplier = currentheight / defaultheight

        footheight = currentheight * footfactor
        footheight_m = fromSVacc(footheight)
        footheight_u = fromSVUSA(footheight)

        toeheight = currentheight * footthickfactor
        toeheight_m = fromSVacc(toeheight)
        toeheight_u = fromSVUSA(toeheight)

        calculatedweight = (baseweight * (multiplier ** 3)) * density
        calculatedweight_m = fromWV(calculatedweight)
        calculatedweight_u = fromWVUSA(calculatedweight)

        relativedefaultheight = defaultheight / defmultiplier
        relativedefaultheight_m = fromSVacc(relativedefaultheight)
        relativedefaultheight_u = fromSVUSA(relativedefaultheight)

        relativedefaultweight = defaultweight / defmultiplier
        relativedefaultweight_m = fromSVacc(relativedefaultweight)
        relativedefaultweight_u = fromSVUSA(relativedefaultweight)

        thumbwidth = currentheight * thumbfactor
        thumbwidth_m = fromSVacc(thumbwidth)
        thumbwidth_u = fromSVUSA(thumbwidth)

        footlength = currentheight * footfactor
        footlength_m = fromSV(footlength)
        footlength_u = fromSVUSA(footlength)

        footwidth = currentheight * footwidthfactor
        footwidth_m = fromSV(footwidth)
        footwidth_u = fromSVUSA(footwidth)

        shoesize = toShoeSize(footlength)

        fingerprintdepth = currentheight * fingerprintfactor
        fingerprintdepth_m = fromSVacc(fingerprintdepth)
        fingerprintdepth_u = fromSVUSA(fingerprintdepth)

        hairwidth = currentheight * hairwidthfactor
        hairwidth_m = fromSVacc(hairwidth)
        hairwidth_u = fromSVUSA(hairwidth)

        pointer = currentheight * pointerfactor
        pointer_m = fromSVUSA(pointer)
        pointer_u = fromSVacc(pointer)

        if multiplier > Decimal("1E15"):
            multiplier_x = f"{multiplier:.2e}"
        else:
            multiplier_x = f"{multiplier:,.4}"

        if defmultiplier > Decimal("1E15"):
            defmultiplier_x = f"{defmultiplier:.2e}"
        else:
            defmultiplier_x = f"{defmultiplier:,.4}"

        if (multiplier ** 3) > Decimal("1E15"):
            multipliercubed_x = f"{(multiplier ** 3):.2e}"
        else:
            multipliercubed_x = f"{(multiplier ** 3):,.4}"

        if (defmultiplier ** 3) > Decimal("1E15"):
            defmultipliercubed_x = f"{(defmultiplier ** 3):.2e}"
        else:
            defmultipliercubed_x = f"{(defmultiplier ** 3):,.4}"

        return (
            f"**{usertag} Stats:**\n"
            f"Current Height: {currentheight_m} / {currentheight_u} ({multiplier_x}x character base, {defmultiplier_x}x average)\n"
            f"Current Weight: {calculatedweight_m} / {calculatedweight_u} ({multipliercubed_x}x charbase, {defmultipliercubed_x}x average)\n"
            f"Current Density: {density}x\n"
            f"Foot Length: {footheight_m} / {footheight_u} ({shoesize})\n"
            f"Foot Width: {footwidth_m} / {footwidth_u}\n"
            f"Toe Height: {toeheight_m} / {toeheight_u}\n"
            f"Pointer Finger Length: {pointer_m} / {pointer_u}\n"
            f"Thumb Width: {thumbwidth_m} / {thumbwidth_u}\n"
            f"Fingerprint Depth: {fingerprintdepth_m} / {fingerprintdepth_u}\n"
            f"Hair Width: {hairwidth_m} / {hairwidth_u}\n"
            f"Size of a Normal Man (Comparative) {relativedefaultheight_m} / {relativedefaultheight_u}\n"
            f"Weight of a Normal Man (Comparative) {relativedefaultweight_m} / {relativedefaultweight_u}\n"
            f"Character Bases: {baseheight_m} / {baseheight_u} | {baseweight_m} / {baseweight_u}")

    @stats.error
    @logger.err2console
    async def stats_handler(self, ctx, error):
        if isinstance(error, InvalidOperation):
            await ctx.send(
                "SizeBot cannot perform this action due to a math error.\n"
                f"Are you too big, {ctx.message.author.id}?")
        else:
            await ctx.send(f"Error? {error}")

    @compare.error
    @logger.err2console
    async def compare_handler(self, ctx, error):
        await ctx.send(f"Error? {error}")


# Necessary
def setup(bot):
    bot.add_cog(StatsCog(bot))
