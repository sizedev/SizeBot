from decimal import InvalidOperation
import math

import discord
from discord.ext import commands
from discord import typing

from sizebot.digidecimal import Decimal
from sizebot import digilogger as logger
# TODO: Fix this...
from sizebot import userdb
from sizebot import digiSV

# TODO: Move to units module
# Conversion constants
footfactor = Decimal(1) / Decimal(7)
footwidthfactor = footfactor / Decimal(2.5)
toeheightfactor = Decimal(1) / Decimal(65)
thumbfactor = Decimal(1) / Decimal(69.06)
fingerprintfactor = Decimal(1) / Decimal(35080)
hairfactor = Decimal(1) / Decimal(23387)
pointerfactor = Decimal(1) / Decimal(17.26)
footthickfactor = Decimal(1)  # TODO: Provide a real value
hairwidthfactor = Decimal(1)  # TODO: Provide a real value


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def stats(self, ctx, memberOrHeight: typing.Union[discord.Member, digiSV.SV] = None):
        if memberOrHeight is None:
            memberOrHeight = ctx.message.author

        if isinstance(memberOrHeight, discord.Member):
            userdata = userdb.load(memberOrHeight.id)
        else:
            userdata = userdb.User()
            userdata.nickname = "Raw"
            userdata.height = memberOrHeight

        output = getStats(userdata)
        await ctx.send(output)
        await logger.info(f"Stats for {memberOrHeight} sent.")

    @commands.command()
    async def compare(self, ctx, memberOrHeight1: typing.Union[discord.Member, digiSV.SV] = None, memberOrHeight2: typing.Union[discord.Member, digiSV.SV] = None):
        if memberOrHeight2 is None:
            memberOrHeight2 = ctx.message.author

        # TODO: Handle this in an error handler
        if memberOrHeight1 is None:
            await ctx.send("Please use either two parameters to compare two people or sizes, or one to compare with yourself.", delete_after = 5)
            return

        if isinstance(memberOrHeight1, discord.Member):
            userdata1 = userdb.load(memberOrHeight1.id)
        else:
            userdata1 = userdb.User()
            userdata1.nickname = "Raw"
            userdata1.height = memberOrHeight1

        if isinstance(memberOrHeight2, discord.Member):
            userdata2 = userdb.load(memberOrHeight2.id)
        else:
            userdata2 = userdb.User()
            userdata2.nickname = "Raw"
            userdata2.height = memberOrHeight2

        output = self.compareUsers(userdata1, userdata2)
        await ctx.send(output)
        await logger.info(f"Compared {userdata1} and {userdata2}")

    @stats.error
    async def stats_handler(self, ctx, error):
        # TODO: Track down what line is causing this
        if isinstance(error, InvalidOperation):
            await ctx.send(
                "SizeBot cannot perform this action due to a math error.\n"
                f"Are you too big, {ctx.message.author.id}?")
        else:
            raise error


# TODO: Clean this up
def compareUsers(userdata1, userdata2):
    if userdata1.height == userdata2.height:
        return f"{userdata1.tag} and {userdata2.tag} match 1 to 1."

    # Who's taller?
    if userdata1.height > userdata2.height:
        biguser = userdata1
        bigusertag = userdata1.tag
        smalluser = userdata2
        smallusertag = userdata2.tag
    else:
        biguser = userdata2
        bigusertag = userdata2.tag
        smalluser = userdata1
        smallusertag = userdata1.tag

    # Compare math
    bigmult = (biguser.height / biguser.baseheight)
    smallmult = (smalluser.height / smalluser.baseheight)
    bigmultcubed = (bigmult ** Decimal("3"))
    smallmultcubed = (smallmult ** Decimal("3"))
    dispbigmult = round(bigmult, Decimal("4"))
    dispsmallmult = round(smallmult, Decimal("4"))
    dispbigmultcubed = round(bigmultcubed, Decimal("4"))
    dispsmallmultcubed = round(smallmultcubed, Decimal("4"))
    bcw = biguser.baseweight * (bigmult ** Decimal("3")) * biguser.density
    scw = smalluser.baseweight * (smallmult ** Decimal("3")) * smalluser.density
    diffmult = bigmult / smallmult
    b2sh = biguser.baseheight * diffmult
    s2bh = smalluser.baseheight / diffmult
    b2sw = biguser.baseweight * (diffmult ** Decimal("3"))
    s2bw = smalluser.baseweight / (diffmult ** Decimal("3"))
    bigtosmallheight = digiSV.fromSV(b2sh, "m", Decimal("3"))
    smalltobigheight = digiSV.fromSV(s2bh, "m", Decimal("3"))
    bigtosmallheightUSA = digiSV.fromSV(b2sh, "u")
    smalltobigheightUSA = digiSV.fromSV(s2bh), "u"
    bigtosmallfoot = digiSV.fromSV(b2sh * footfactor, "m", Decimal("3"))
    smalltobigfoot = digiSV.fromSV(s2bh * footfactor, "m", Decimal("3"))
    bigtosmallfootUSA = digiSV.fromSV(b2sh * footfactor, "u")
    smalltobigfootUSA = digiSV.fromSV(s2bh * footfactor, "u")
    bigtosmallshoe = digiSV.toShoeSize(b2sh * footfactor / digiSV.inch)
    smalltobigshoe = digiSV.toShoeSize(s2bh * footfactor / digiSV.inch)
    bigtosmallweight = digiSV.fromWV(b2sw, "m")
    smalltobigweight = digiSV.fromWV(s2bw, "m")
    bigtosmallweightUSA = digiSV.fromWV(b2sw, "u")
    smalltobigweightUSA = digiSV.fromWV(s2bw, "u")
    bigtosmallfootwidth = digiSV.fromSV(b2sh * footwidthfactor, "m", Decimal("3"))
    smalltobigfootwidth = digiSV.fromSV(s2bh * footwidthfactor, "m", Decimal("3"))
    bigtosmallfootwidthUSA = digiSV.fromSV(b2sh * footwidthfactor, "u")
    smalltobigfootwidthUSA = digiSV.fromSV(s2bh * footwidthfactor, "u")
    bigtosmallfootthick = digiSV.fromSV(b2sh * footthickfactor, "m", Decimal("3"))
    smalltobigfootthick = digiSV.fromSV(s2bh * footthickfactor, "m", Decimal("3"))
    bigtosmallfootthickUSA = digiSV.fromSV(b2sh * footthickfactor, "u")
    smalltobigfootthickUSA = digiSV.fromSV(s2bh * footthickfactor, "u")
    bigtosmallthumb = digiSV.fromSV(b2sh * thumbfactor, "m", Decimal("3"))
    smalltobigthumb = digiSV.fromSV(s2bh * thumbfactor, "m", Decimal("3"))
    bigtosmallthumbUSA = digiSV.fromSV(b2sh * thumbfactor, "u")
    smalltobigthumbUSA = digiSV.fromSV(s2bh * thumbfactor, "u")
    bigtosmallfingerprint = digiSV.fromSV(b2sh * fingerprintfactor, "m", Decimal("3"))
    smalltobigfingerprint = digiSV.fromSV(s2bh * fingerprintfactor, "m", Decimal("3"))
    bigtosmallfingerprintUSA = digiSV.fromSV(b2sh * fingerprintfactor, "u")
    smalltobigfingerprintUSA = digiSV.fromSV(s2bh * fingerprintfactor, "u")
    bigtosmallhairwidth = digiSV.fromSV(b2sh * hairwidthfactor, "m", Decimal("3"))
    smalltobighairwidth = digiSV.fromSV(s2bh * hairwidthfactor, "m", Decimal("3"))
    bigtosmallhairwidthUSA = digiSV.fromSV(b2sh * hairwidthfactor, "u")
    smalltobighairwidthUSA = digiSV.fromSV(s2bh * hairwidthfactor, "u")
    bigtosmallpointer = digiSV.fromSV(b2sh * pointerfactor, "m", Decimal("3"))
    smalltobigpointer = digiSV.fromSV(s2bh * pointerfactor, "m", Decimal("3"))
    bigtosmallpointerUSA = digiSV.fromSV(b2sh * pointerfactor, "u")
    smalltobigpointerUSA = digiSV.fromSV(s2bh * pointerfactor, "u")
    timestaller = digiSV.placeValue(round((biguser.height / smalluser.height), Decimal("3")))

    # Print compare
    enspace = "\u2002"
    printtab = enspace * 4

    return (
        "**Comparison:**\n"
        f"{bigusertag} is really:\n"
        f"{printtab}Real Height: {digiSV.fromSV(biguser.height, 'm', 3)} / {digiSV.fromSV(biguser.height, 'u')} ({digiSV.placeValue(dispbigmult)}x basesize)\n"
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
        f"{printtab}Real Height: {digiSV.fromSV(smalluser.height, 'm', 3)} / {digiSV.fromSV(smalluser.height, 'u')} ({digiSV.placeValue(dispsmallmult)}x basesize)\n"
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
        f"{printtab}{bigusertag}: {digiSV.fromSV(biguser.baseheight, 'm', 3)} / {digiSV.fromSV(biguser.baseheight, 'u')} | {digiSV.fromWV(biguser.baseweight, 'm')} / {digiSV.fromWV(biguser.baseweight, 'u')}\n"
        f"{printtab}{smallusertag}: {digiSV.fromSV(smalluser.baseheight, 'm', 3)} / {digiSV.fromSV(smalluser.baseheight, 'u')} | {digiSV.fromWV(smalluser.baseweight, 'm')} / {digiSV.fromWV(smalluser.baseweight, 'u')}")


# TODO: Clean this up
def getStats(userdata):
    multiplier = userdata.height / userdata.baseheight
    multiplier3 = multiplier ** 3

    baseheight_m = digiSV.fromSV(userdata.baseheight, "m", 3)
    baseheight_u = digiSV.fromSV(userdata.baseheight, "u", 3)
    baseweight_m = digiSV.fromWV(userdata.baseweight, "m", 3)
    baseweight_u = digiSV.fromWV(userdata.baseweight, "u", 3)
    currentheight_m = digiSV.fromSV(userdata.height, "m", 3)
    currentheight_u = digiSV.fromSV(userdata.height, "u", 3)

    currentweight = userdata.baseweight * multiplier3 * userdata.density
    currentweight_m = digiSV.fromWV(currentweight, "m", 3)
    currentweight_u = digiSV.fromWV(currentweight, "u", 3)

    printdensity = round(userdata.density, 3)

    defaultheightmult = userdata.height / userdb.defaultheight
    defaultweightmult = currentweight / userdb.defaultweight ** 3

    footlength_m = digiSV.fromSV(userdata.height * footfactor, "m", 3)
    footlength_u = digiSV.fromSV(userdata.height * footfactor, "u", 3)

    footwidth_m = digiSV.fromSV(userdata.height * footwidthfactor, "m", 3)
    footwidth_u = digiSV.fromSV(userdata.height * footwidthfactor, "u", 3)
    toeheight_m = digiSV.fromSV(userdata.height * toeheightfactor, "m", 3)
    toeheight_u = digiSV.fromSV(userdata.height * toeheightfactor, "u", 3)

    pointer_m = digiSV.fromSV(userdata.height * pointerfactor, "m", 3)
    pointer_u = digiSV.fromSV(userdata.height * pointerfactor, "u", 3)
    thumb_m = digiSV.fromSV(userdata.height * thumbfactor, "m", 3)
    thumb_u = digiSV.fromSV(userdata.height * thumbfactor, "u", 3)
    fingerprint_m = digiSV.fromSV(userdata.height * fingerprintfactor, "m", 3)
    fingerprint_u = digiSV.fromSV(userdata.height * fingerprintfactor, "u", 3)

    hair_m = digiSV.fromSV(userdata.height * hairfactor, "m", 3)
    hair_u = digiSV.fromSV(userdata.height * hairfactor, "u", 3)

    normalheightcomp_m = digiSV.fromSV(userdb.defaultheight / defaultheightmult, "m", 3)
    normalheightcomp_u = digiSV.fromSV(userdb.defaultheight / defaultheightmult, "u", 3)
    normalweightcomp_m = digiSV.fromWV(userdb.defaultweight / defaultweightmult, "m", 3)

    tallerheight = max(userdata.height, userdb.defaultheight)
    smallerheight = min(userdata.height, userdb.defaultheight)
    if userdata.height >= userdb.defaultheight:
        lookdirection = "down"
    else:
        lookdirection = "up"

    # This is disgusting, but it works!
    lookangle = str(round(math.degrees(math.atan((tallerheight - smallerheight) / (tallerheight / 2))), 0)).split(".")[0]

    return (
        f"**{userdata.tag} Stats:\n"
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


# Necessary
def setup(bot):
    bot.add_cog(StatsCog(bot))
