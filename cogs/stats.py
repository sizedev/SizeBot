from decimal import Decimal
import decimal
import math

from discord.ext import commands

import digilogger as logger
import digiformatter as df
# TODO: Fix this...
import userdb
from userdb import CHEI, BHEI, BWEI, DENS
from globalsb import printtab
import digiSV

# TODO: Move to units module.
# Conversion constants.
footfactor = Decimal(1) / Decimal(7)
footwidthfactor = footfactor / Decimal(2.5)
toeheightfactor = Decimal(1) / Decimal(65)
thumbfactor = Decimal(1) / Decimal(69.06)
fingerprintfactor = Decimal(1) / Decimal(35080)
hairfactor = Decimal(1) / Decimal(23387)
pointerfactor = Decimal(1) / Decimal(17.26)
footthickfactor = Decimal(1)  # TODO: Provide a real value
hairwidthfactor = Decimal(1)  # TODO: Provide a real value


# TODO: Move to dedicated module.
async def getUser(ctx, user_string, fakename=None):
    try:
        member = await commands.MemberConverter().convert(ctx, user_string)
    except commands.errors.BadArgument:
        member = None

    if fakename is None:
        fakename = "Raw"

    if member:
        usertag = f"<@{member.id}>"
        userdata = userdb.load(member.id)
    else:
        usertag = fakename
        heightsv = digiSV.toSV(user_string)
        if heightsv is None:
            await ctx.send(
                "Sorry! I didn't recognize that user or height.",
                delete_after=5)
            return None, None

        userdata = userdb.User()
        userdata.nickname = fakename
        userdata.height = heightsv

    return usertag, userdata


# TODO: Clean this up.
def userStats(usertag, userid):
    userdata = userdb.load(userid)
    # usernick = userdata[NICK]                  # TODO: Unused
    # userdisplay = userdata[DISP]               # TODO: Unused
    userbaseheight = Decimal(userdata[BHEI])
    userbaseweight = Decimal(userdata[BWEI])
    usercurrentheight = Decimal(userdata[CHEI])
    userdensity = Decimal(userdata[DENS])
    # userspecies = userdata[SPEC]               # TODO: Unused

    multiplier = usercurrentheight / userbaseheight
    # multiplier2 = multiplier ** 2               # TODO: Unused
    multiplier3 = multiplier ** 3

    baseheight_m = digiSV.fromSV(userbaseheight, 'm', 3)
    baseheight_u = digiSV.fromSV(userbaseheight, 'u', 3)
    baseweight_m = digiSV.fromWV(userbaseweight, 'm', 3)
    baseweight_u = digiSV.fromWV(userbaseweight, 'u', 3)
    currentheight_m = digiSV.fromSV(usercurrentheight, 'm', 3)
    currentheight_u = digiSV.fromSV(usercurrentheight, 'u', 3)

    currentweight = userbaseweight * multiplier3 * userdensity
    currentweight_m = digiSV.fromWV(currentweight, 'm', 3)
    currentweight_u = digiSV.fromWV(currentweight, 'u', 3)

    printdensity = round(userdensity, 3)

    defaultheightmult = usercurrentheight / userdb.defaultheight
    defaultweightmult = currentweight / userdb.defaultweight ** 3

    footlength_m = digiSV.fromSV(usercurrentheight * footfactor, 'm', 3)
    footlength_u = digiSV.fromSV(usercurrentheight * footfactor, 'u', 3)
    # footlengthinches = usercurrentheight * footfactor / digiSV.inch # TODO: Unused
    # shoesize = digiSV.toShoeSize(footlengthinches) # TODO: Unused
    footwidth_m = digiSV.fromSV(usercurrentheight * footwidthfactor, 'm', 3)
    footwidth_u = digiSV.fromSV(usercurrentheight * footwidthfactor, 'u', 3)
    toeheight_m = digiSV.fromSV(usercurrentheight * toeheightfactor, 'm', 3)
    toeheight_u = digiSV.fromSV(usercurrentheight * toeheightfactor, 'u', 3)

    pointer_m = digiSV.fromSV(usercurrentheight * pointerfactor, 'm', 3)
    pointer_u = digiSV.fromSV(usercurrentheight * pointerfactor, 'u', 3)
    thumb_m = digiSV.fromSV(usercurrentheight * thumbfactor, 'm', 3)
    thumb_u = digiSV.fromSV(usercurrentheight * thumbfactor, 'u', 3)
    fingerprint_m = digiSV.fromSV(usercurrentheight * fingerprintfactor, 'm', 3)
    fingerprint_u = digiSV.fromSV(usercurrentheight * fingerprintfactor, 'u', 3)

    hair_m = digiSV.fromSV(usercurrentheight * hairfactor, 'm', 3)
    hair_u = digiSV.fromSV(usercurrentheight * hairfactor, 'u', 3)

    normalheightcomp_m = digiSV.fromSV(userdb.defaultheight / defaultheightmult, 'm', 3)
    normalheightcomp_u = digiSV.fromSV(userdb.defaultheight / defaultheightmult, 'u', 3)
    normalweightcomp_m = digiSV.fromWV(userdb.defaultweight / defaultweightmult, 'm', 3)
    # normalweightcomp_u = fromWVUSA(userdb.defaultweight / defaultweightmult, 3)  # TODO: Unused

    tallerheight = 0
    smallerheight = 0
    lookdirection = ""
    if usercurrentheight >= userdb.defaultheight:
        tallerheight = usercurrentheight
        smallerheight = userdb.defaultheight
        lookdirection = "down"
    else:
        tallerheight = userdb.defaultheight
        smallerheight = usercurrentheight
        lookdirection = "up"

    # This is disgusting, but it works!
    lookangle = str(round(math.degrees(math.atan((tallerheight - smallerheight) / (tallerheight / 2))), 0)).split(".")[0]

    return (
        f"**{usertag} Stats:\n"
        f"*Current Height:*  {currentheight_m} / {currentheight_u}\n"
        f"*Current Weight:*  {currentweight_m} / {currentweight_u}\n"
        f"*Current Density:* {printdensity}x\n"
        f"\n"
        f"Foot Length: {footlength_m} / {footlength_u}\n"
        f"Foot Width: {footwidth_m} / {footwidth_u}\n"
        f"Toe Height: {toeheight_m} / {toeheight_u}\n"
        f"Pointer Finger Length: {pointer_m} / {pointer_u}\n"
        f"Thumb Width: {thumb_m} / {thumb_u}\n"
        f"Fingerprint Depth: {fingerprint_m} / {fingerprint_u}\n"
        f"Hair Width: {hair_m} / {hair_u}\n"
        f"\n"
        f"Size of a Normal Man (Comparative): {normalheightcomp_m} / {normalheightcomp_u}\n"
        f"Weight of a Normal Man (Comparative): {normalweightcomp_m} / {normalheightcomp_u}\n"
        f"To look {lookdirection} at a average human, you'd have to look {lookdirection} {lookangle}°.\n"
        f"\n"
        f"Character Bases: {baseheight_m} / {baseheight_u} | {baseweight_m} / {baseweight_u}"
    )


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

        output = userStats(user1tag, user1)
        await ctx.send(output)
        df.msg(f"Stats for {who} sent.")

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
        bigtosmallheight = digiSV.fromSV(b2sh, 'm', 3)
        smalltobigheight = digiSV.fromSV(s2bh, 'm', 3)
        bigtosmallheightUSA = digiSV.fromSV(b2sh, 'u')
        smalltobigheightUSA = digiSV.fromSV(s2bh), 'u'
        bigtosmallfoot = digiSV.fromSV(b2sh * footfactor, 'm', 3)
        smalltobigfoot = digiSV.fromSV(s2bh * footfactor, 'm', 3)
        bigtosmallfootUSA = digiSV.fromSV(b2sh * footfactor, 'u')
        smalltobigfootUSA = digiSV.fromSV(s2bh * footfactor, 'u')
        bigtosmallshoe = digiSV.toShoeSize(b2sh * footfactor / digiSV.inch)
        smalltobigshoe = digiSV.toShoeSize(s2bh * footfactor / digiSV.inch)
        bigtosmallweight = digiSV.fromWV(b2sw, 'm')
        smalltobigweight = digiSV.fromWV(s2bw, 'm')
        bigtosmallweightUSA = digiSV.fromWV(b2sw, 'u')
        smalltobigweightUSA = digiSV.fromWV(s2bw, 'u')
        bigtosmallfootwidth = digiSV.fromSV(b2sh * footwidthfactor, 'm', 3)
        smalltobigfootwidth = digiSV.fromSV(s2bh * footwidthfactor, 'm', 3)
        bigtosmallfootwidthUSA = digiSV.fromSV(b2sh * footwidthfactor, 'u')
        smalltobigfootwidthUSA = digiSV.fromSV(s2bh * footwidthfactor, 'u')
        bigtosmallfootthick = digiSV.fromSV(b2sh * footthickfactor, 'm', 3)
        smalltobigfootthick = digiSV.fromSV(s2bh * footthickfactor, 'm', 3)
        bigtosmallfootthickUSA = digiSV.fromSV(b2sh * footthickfactor, 'u')
        smalltobigfootthickUSA = digiSV.fromSV(s2bh * footthickfactor, 'u')
        bigtosmallthumb = digiSV.fromSV(b2sh * thumbfactor, 'm', 3)
        smalltobigthumb = digiSV.fromSV(s2bh * thumbfactor, 'm', 3)
        bigtosmallthumbUSA = digiSV.fromSV(b2sh * thumbfactor, 'u')
        smalltobigthumbUSA = digiSV.fromSV(s2bh * thumbfactor, 'u')
        bigtosmallfingerprint = digiSV.fromSV(b2sh * fingerprintfactor, 'm', 3)
        smalltobigfingerprint = digiSV.fromSV(s2bh * fingerprintfactor, 'm', 3)
        bigtosmallfingerprintUSA = digiSV.fromSV(b2sh * fingerprintfactor, 'u')
        smalltobigfingerprintUSA = digiSV.fromSV(s2bh * fingerprintfactor, 'u')
        bigtosmallhairwidth = digiSV.fromSV(b2sh * hairwidthfactor, 'm', 3)
        smalltobighairwidth = digiSV.fromSV(s2bh * hairwidthfactor, 'm', 3)
        bigtosmallhairwidthUSA = digiSV.fromSV(b2sh * hairwidthfactor, 'u')
        smalltobighairwidthUSA = digiSV.fromSV(s2bh * hairwidthfactor, 'u')
        bigtosmallpointer = digiSV.fromSV(b2sh * pointerfactor, 'm', 3)
        smalltobigpointer = digiSV.fromSV(s2bh * pointerfactor, 'm', 3)
        bigtosmallpointerUSA = digiSV.fromSV(b2sh * pointerfactor, 'u')
        smalltobigpointerUSA = digiSV.fromSV(s2bh * pointerfactor, 'u')
        timestaller = digiSV.placeValue(round((bch / sch), 3))

        # Print compare.
        return (
            "**Comparison:**\n"
            f"{bigusertag} is really:\n"
            f"{printtab}Real Height: {digiSV.fromSV(bch, 'm', 3)} / {digiSV.fromSV(bch, 'u')} ({digiSV.placeValue(dispbigmult)}x basesize)\n"
            f"{printtab}Real Weight: {digiSV.fromWV(bcw, 'm')} / {digiSV.fromWV(bcw, 'u')}. ({digiSV.placeValue(dispbigmultcubed)}x basesize)\n"
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
            f"{printtab}Real Height: {digiSV.fromSV(sch, 'm', 3)} / {digiSV.fromSV(sch, 'u')} ({digiSV.placeValue(dispsmallmult)}x basesize)\n"
            f"{printtab}Real Weight: {digiSV.fromWV(scw, 'm')} / {digiSV.fromWV(scw, 'u')}. ({digiSV.placeValue(dispsmallmultcubed)}x basesize)\n"
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
            f"{printtab}{bigusertag}: {digiSV.fromSV(bbh, 'm', 3)} / {digiSV.fromSV(bbh, 'u')} | {digiSV.fromWV(bbw, 'm')} / {digiSV.fromWV(bbw, 'u')}\n"
            f"{printtab}{smallusertag}: {digiSV.fromSV(sbh, 'm', 3)} / {digiSV.fromSV(sbh, 'u')} | {digiSV.fromWV(sbw, 'm')} / {digiSV.fromWV(sbw, 'u')}")

    @stats.error
    @logger.err2console
    async def stats_handler(self, ctx, error):
        if isinstance(error, decimal.InvalidOperation):
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
