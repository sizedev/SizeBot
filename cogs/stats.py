import os
from decimal import Decimal, InvalidOperation

import discord
from discord.ext import commands

# TODO: Fix this...
from globalsb import NICK, DISP, CHEI, BHEI, BWEI, DENS, UNIT, SPEC
from globalsb import readUser, folder, getNum, getLet, isFeetAndInchesAndIfSoFixIt, placeValue
from globalsb import defaultheight, defaultweight, defaultdensity, inch
from globalsb import fromSV, fromSVUSA, fromWV, fromWVUSA, toShoeSize, toSV
from globalsb import printtab

import digilogger as logger
import digiformatter as df

# TODO: Move to units module.
# Conversion constants.
footfactor = Decimal(1) / Decimal(7)
footwidthfactor = footfactor / Decimal(2.5)
toeheightfactor = Decimal(1) / Decimal(65)
thumbfactor = Decimal(1) / Decimal(69.06)
fingerprintfactor = Decimal(1) / Decimal(35080)
hairfactor = Decimal(1) / Decimal(23387)
pointerfactor = Decimal(1) / Decimal(17.26)


# TODO: Move to dedicated module.
async def getUser(ctx, user_string, fakename = None):
    try:
        member = await commands.MemberConverter().convert(ctx, user_string)
    except commands.errors.BadArgument:
        member = None

    if fakename == None:
        fakename = "Raw"

    if member:
        usertag = f"<@{member.id}>"
        user = loadUser(member.id)
        if user is None:
            await ctx.send(
                "Sorry! User isn't registered with SizeBot.\n"
                "To register, use the `&register` command.",
                delete_after=5)
            return None, None
    else:
        usertag = fakename
        heightstring = isFeetAndInchesAndIfSoFixIt(user_string)
        height = toSV(getNum(heightstring), getLet(heightstring))
        if height is None:
            await ctx.send(
                "Sorry! I didn't recognize that user or height.",
                delete_after=5)
            return None, None

        user = heightToUser(height, fakename)

    return usertag, user


def loadUser(userid):
    userid = str(userid)
    if not os.path.exists(folder + "/users/" + userid + ".txt"):
        # User file missing
        return None
    user = readUser(userid)
    return user


def heightToUser(height, fakename = None):
    if fakename == None:
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

        user1tag, user1 = await getUser(ctx, who)
        if user1 is None:
            return

        output = self.userStats(user1tag, user1)
        await ctx.send(output)
        df.msg(f"Stats for {who} sent.")

    @commands.command()
    async def compare(self, ctx, who1 = None, who2 = None, who1name = None, who2name = None):
        if who2 is None:
            who2 = str(ctx.message.author.id)

        if who1 is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.", delete_after=5)
            return

        if who1name is None:
            who1name = "Raw 1"

        if who2name is None:
            who2name = "Raw 2"

        user1tag, user1 = await getUser(ctx, who1, who1name)
        if user1 is None:
            await ctx.send(f"{who1} is not a recognized user or size.")
            return
        user2tag, user2 = await getUser(ctx, who2, who2name)
        if user2 is None:
            await ctx.send(f"{who2} is not a recognized user or size.")
            return

        output = self.compareUsers(user1tag, user1, user2tag, user2)
        await ctx.send(output)
        df.msg(f"Compared {user1} and {user2}")

    # TODO: Clean this up.
    def compareUsers(self, user1tag, user1, user2tag, user2):
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
        bigtosmallheight = fromSV(b2sh, 3)
        smalltobigheight = fromSV(s2bh, 3)
        bigtosmallheightUSA = fromSVUSA(b2sh)
        smalltobigheightUSA = fromSVUSA(s2bh)
        bigtosmallfoot = fromSV(b2sh * footfactor, 3)
        smalltobigfoot = fromSV(s2bh * footfactor, 3)
        bigtosmallfootUSA = fromSVUSA(b2sh * footfactor)
        smalltobigfootUSA = fromSVUSA(s2bh * footfactor)
        bigtosmallshoe = toShoeSize(b2sh * footfactor / inch)
        smalltobigshoe = toShoeSize(s2bh * footfactor / inch)
        bigtosmallweight = fromWV(b2sw)
        smalltobigweight = fromWV(s2bw)
        bigtosmallweightUSA = fromWVUSA(b2sw)
        smalltobigweightUSA = fromWVUSA(s2bw)
        bigtosmallfootwidth = fromSV(b2sh * footwidthfactor, 3)
        smalltobigfootwidth = fromSV(s2bh * footwidthfactor, 3)
        bigtosmallfootwidthUSA = fromSVUSA(b2sh * footwidthfactor)
        smalltobigfootwidthUSA = fromSVUSA(s2bh * footwidthfactor)
        bigtosmallfootthick = fromSV(b2sh * footthickfactor, 3)
        smalltobigfootthick = fromSV(s2bh * footthickfactor, 3)
        bigtosmallfootthickUSA = fromSVUSA(b2sh * footthickfactor)
        smalltobigfootthickUSA = fromSVUSA(s2bh * footthickfactor)
        bigtosmallthumb = fromSV(b2sh * thumbfactor, 3)
        smalltobigthumb = fromSV(s2bh * thumbfactor, 3)
        bigtosmallthumbUSA = fromSVUSA(b2sh * thumbfactor)
        smalltobigthumbUSA = fromSVUSA(s2bh * thumbfactor)
        bigtosmallfingerprint = fromSV(b2sh * fingerprintfactor, 3)
        smalltobigfingerprint = fromSV(s2bh * fingerprintfactor, 3)
        bigtosmallfingerprintUSA = fromSVUSA(b2sh * fingerprintfactor)
        smalltobigfingerprintUSA = fromSVUSA(s2bh * fingerprintfactor)
        bigtosmallhairwidth = fromSV(b2sh * hairwidthfactor, 3)
        smalltobighairwidth = fromSV(s2bh * hairwidthfactor, 3)
        bigtosmallhairwidthUSA = fromSVUSA(b2sh * hairwidthfactor)
        smalltobighairwidthUSA = fromSVUSA(s2bh * hairwidthfactor)
        bigtosmallpointer = fromSV(b2sh * pointerfactor, 3)
        smalltobigpointer = fromSV(s2bh * pointerfactor, 3)
        bigtosmallpointerUSA = fromSVUSA(b2sh * pointerfactor)
        smalltobigpointerUSA = fromSVUSA(s2bh * pointerfactor)
        timestaller = placeValue(round((bch / sch), 3))

        # Print compare.
        return (
            "**Comparison:**\n"
            f"{bigusertag} is really:\n"
            f"{printtab}Real Height: {fromSV(bch, 3)} / {fromSVUSA(bch)} ({placeValue(dispbigmult)}x basesize)\n"
            f"{printtab}Real Weight: {fromWV(bcw)} / {fromWVUSA(bcw)}. ({placeValue(dispbigmultcubed)}x basesize)\n"
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
            f"{printtab}Real Height: {fromSV(sch, 3)} / {fromSVUSA(sch)} ({placeValue(dispsmallmult)}x basesize)\n"
            f"{printtab}Real Weight: {fromWV(scw)} / {fromWVUSA(scw)}. ({placeValue(dispsmallmultcubed)}x basesize)\n"
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
            f"{printtab}{bigusertag}: {fromSV(bbh, 3)} / {fromSVUSA(bbh)} | {fromWV(bbw)} / {fromWVUSA(bbw)}\n"
            f"{printtab}{smallusertag}: {fromSV(sbh, 3)} / {fromSVUSA(sbh)} | {fromWV(sbw)} / {fromWVUSA(sbw)}")

    # TODO: Clean this up.
    def userStats(self, user1tag, user1):
            userattrs = readUser(user1)
            usernick = userattrs[NICK]
            userdisplay = userattrs[DISP]
            userbaseheight = Decimal(userattrs[BHEI])
            userbaseweight = Decimal(userattrs[BWEI])
            usercurrentheight = Decimal(userattrs[CHEI])
            userdensity = Decimal(userattrs[DENS])
            userspecies = userattrs[SPEC]

            multiplier = userattrs[CHEI] / userattrs[BHEI]
            multiplier2 = multiplier ** 2
            multiplier3 = multiplier ** 3

            baseheight_m = fromSV(userattrs[BHEI], 3)
            baseheight_u = fromSVUSA(userattrs[BHEI], 3)
            baseweight_m = fromWV(userattrs[BWEI], 3)
            baseweight_u = fromWVUSA(userattrs[BWEI], 3)
            currentheight_m = fromSV(userattrs[CHEI], 3)
            currentheight_u = fromSVUSA(userattrs[CHEI], 3)

            currentweight = userbaseweight * multiplier3 * userdensity
            currentweight_m = fromSV(currentweight, 3)
            currentweight_u = fromSVUSA(currentweight, 3)

            footlength_m = fromSV(usercurrentheight * footfactor, 3)
            footlength_u = fromSVUSA(usercurrentheight * footfactor, 3)
            footlengthinches = usercurrentheight * footfactor / inch
            shoesize = toShoeSize(footlengthinches)
            footwidth_m = fromSV(usercurrentheight * footwidthfactor, 3)
            footwidth_u = fromSVUSA(usercurrentheight * footwidthfactor, 3)
            toeheight_m = fromSV(usercurrentheight * toeheightfactor, 3)
            toeheight_u = fromSVUSA(usercurrentheight * toeheightfactor, 3)

            pointer_m = fromSV(usercurrentheight * pointerfactor, 3)
            pointer_u = fromSVUSA(usercurrentheight * pointerfactor, 3)
            thumb_m = fromSV(usercurrentheight * thumbfactor, 3)
            thumb_u = fromSVUSA(usercurrentheight * thumbfactor, 3)
            fingerprint_m = fromSV(usercurrentheight * fingerprintfactor, 3)
            fingerprint_u = fromSVUSA(usercurrentheight * fingerprintfactor, 3)

            hair_m = fromSV(usercurrentheight * hairfactor, 3)
            hair_u = fromSVUSA(usercurrentheight * hairfactor, 3)

            normalheightcomp_m = toSV(0, 3)
            normalheightcomp_u = toSV(0, 3)
            normalweightcomp_m = toWV(0, 3)
            normalweightcomp_u = toWV(0, 3)


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
