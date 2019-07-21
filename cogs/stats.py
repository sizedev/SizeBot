import os
from decimal import Decimal, InvalidOperation

import discord
from discord.ext import commands

# TODO: Fix this...
from globalsb import NICK, DISP, CHEI, BHEI, BWEI, DENS, UNIT, SPEC
from globalsb import read_user, folder, getnum, getlet, isFeetAndInchesAndIfSoFixIt, place_value
from globalsb import defaultheight, defaultweight, defaultdensity, inch
from globalsb import fromSVacc, fromSVUSA, fromSV, fromWV, fromWVUSA, toShoeSize, toSV

import digilogger as logger

# TODO: Move to units module
# Conversion constants
footfactor = Decimal(1) / Decimal(7)
footwidthfactor = footfactor / Decimal(2.5)
footthickfactor = Decimal(1) / Decimal(65)
thumbfactor = defaultheight / inch
fingerprintfactor = Decimal(1) / Decimal(35080)
hairwidthfactor = Decimal(1) / Decimal(23387)


# TODO: Move to dedicated module
async def get_user(ctx, user_string):
    try:
        member = await commands.MemberConverter().convert(ctx, user_string)
    except commands.errors.BadArgument:
        member = None

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
        usertag = "Raw"
        heightstring = isFeetAndInchesAndIfSoFixIt(user_string)
        height = toSV(getnum(heightstring), getlet(heightstring))
        if height is None:
            await ctx.send(
                "Sorry! I didn't recognize that user or height.",
                delete_after=5)
            return None, None

        user = height_to_user(height)

    return usertag, user


def load_user(userid):
    userid = str(userid)
    if not os.path.exists(folder + "/users/" + userid + ".txt"):
        # User file missing
        return None
    user = read_user(userid)
    return user


def height_to_user(height):
    user = [
        "Raw\n",
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
        print(f"Stats for {who} sent.")

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
        bigtosmallshoe = toShoeSize(b2sh * footfactor / inch)
        smalltobigshoe = toShoeSize(s2bh * footfactor / inch)
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
        timestaller = place_value(round((bch / sch), 3))

        # Print compare
        return (
            "**Comparison:**\n"
            f"{bigusertag} is really:\n"
            f"  Real Height: {fromSVacc(bch)} / {fromSVUSA(bch)} ({place_value(dispbigmult)}x basesize)\n"
            f"  Real Weight:{fromWV(bcw)} / {fromWVUSA(bcw)}. ({place_value(dispbigmultcubed)}x basesize)\n"
            f"To {smallusertag}, {bigusertag} looks:\n"
            f"  Height: {bigtosmallheight} / {bigtosmallheightUSA}\n"
            f"  Weight: {bigtosmallweight} / {bigtosmallweightUSA}\n"
            f"  Foot Length: {bigtosmallfoot} / {bigtosmallfootUSA} ({bigtosmallshoe})\n"
            f"  Foot Width: {bigtosmallfootwidth} / {bigtosmallfootwidthUSA}\n"
            f"  Toe Height: {bigtosmallfootthick} / {bigtosmallfootthickUSA}\n"
            f"  Thumb Width: {bigtosmallthumb} / {bigtosmallthumbUSA}\n"
            f"  Fingerprint Depth: {bigtosmallfingerprint} / {bigtosmallfingerprintUSA}\n"
            f"  Hair Width: {bigtosmallhairwidth} / {bigtosmallhairwidthUSA}\n"
            "\n"
            f"{bigusertag} is {timestaller}x taller than {smallusertag}.\n"
            "\n"
            f"{smallusertag} is really:\n"
            f"  Real Height: {fromSVacc(sch)} / {fromSVUSA(sch)} ({place_value(dispsmallmult)}x basesize)\n"
            f"  Real Weight:{fromWV(scw)} / {fromWVUSA(scw)}. ({place_value(dispsmallmultcubed)}x basesize)\n"
            f"To {bigusertag}, {smallusertag} looks:\n"
            f"  Height: {smalltobigheight} / {smalltobigheightUSA}\n"
            f"  Weight: {smalltobigweight} / {smalltobigweightUSA}\n"
            f"  Foot Length: {smalltobigfoot} / {smalltobigfootUSA} ({smalltobigshoe})\n"
            f"  Foot Width: {smalltobigfootwidth} / {smalltobigfootwidthUSA}\n"
            f"  Toe Height: {smalltobigfootthick} / {smalltobigfootthickUSA}\n"
            f"  Thumb Width: {smalltobigthumb} / {smalltobigthumbUSA}\n"
            f"  Fingerprint Depth: {smalltobigfingerprint} / {smalltobigfingerprintUSA}\n"
            f"  Hair Width: {smalltobighairwidth} / {smalltobighairwidthUSA}\n"
            "\n"
            f"**Base Sizes:**\n"
            f"{bigusertag}: {fromSVacc(bbh)} / {fromSVUSA(bbh)} | {fromWV(bbw)} / {fromWVUSA(bbw)}\n"
            f"{smallusertag}: {fromSVacc(sbh)} / {fromSVUSA(sbh)} | {fromWV(sbw)} / {fromWVUSA(sbw)}")

    def user_stats(self, user1tag, user1):
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
        shoesize = toShoeSize(footlengthinches)
        fingerprintdepth = fromSVacc(Decimal(user1[CHEI]) * fingerprintfactor)
        fingerprintdepthUSA = fromSVUSA(Decimal(user1[CHEI]) * fingerprintfactor)
        hairwidth = fromSVacc(Decimal(user1[CHEI]) * hairwidthfactor)
        hairwidthUSA = fromSVUSA(Decimal(user1[CHEI]) * hairwidthfactor)
        hcms = place_value(round(multiplier, 4))
        hbms = place_value(round(basemult, 4))
        wcms = place_value(round(multipliercubed * density, 4))
        wbms = place_value(round(basemultcubed * density, 4))
        if multiplier > 999999999999999:
            hcms = "{:.2e}".format(multiplier)
        if basemult > 999999999999999:
            hbms = "{:.2e}".format(basemult)
        if multipliercubed > 999999999999999:
            wcms = "{:.2e}".format(multipliercubed * density)
        if basemultcubed > 999999999999999:
            wbms = "{:.2e}".format(basemultcubed * density)

        return (
            f"**{user1tag} Stats:**\n"
            f"Current Height: {readableheight} | {readableUSAheight} ({hcms}x character base, {hbms}x average)\n"
            f"Current Weight: {readableweight} | {readableUSAweight} ({wcms}x charbase, {wbms}x average)\n"
            f"Current Density: {density}x\n"
            f"Foot Length: {readablefootheight} | {readablefootUSAheight} ({shoesize})\n"
            f"Foot Width: {footwidth} | {footwidthUSA}\n"
            f"Toe Height: {readablefootthick} | {readablefootUSAthick}\n"
            f"Thumb Width: {thumbsize} | {thumbsizeUSA}\n"
            f"Fingerprint Depth: {fingerprintdepth} | {fingerprintdepthUSA}\n"
            f"Hair Width: {hairwidth} | {hairwidthUSA}\n"
            f"Size of a Normal Man (Comparative) {normalheight} | {normalUSAheight}\n"
            f"Weight of a Normal Man (Comparative) {normalweight} | {normalUSAweight}\n"
            f"Character Bases: {userbaseh}, {userbasehusa} | {userbasew}, {userbasewusa}")

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
    @compareraw.error
    @logger.err2console
    async def compare_handler(self, ctx, error):
        await ctx.send(f"Error? {error}")


# Necessary
def setup(bot):
    bot.add_cog(StatsCog(bot))
