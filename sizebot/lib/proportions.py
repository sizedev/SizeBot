from __future__ import annotations
from typing import TypedDict

from discord import Embed

from sizebot import __version__
from sizebot.lib import errors, macrovision, userdb
from sizebot.lib.constants import colors, emojis
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.speed import speedcalc
from sizebot.lib.units import SV, TV
from sizebot.lib.userdb import User
from sizebot.lib.utils import join_unique, minmax
from sizebot.lib.stats import calc_view_angle, statmap, StatBox


compareicon = "https://media.discordapp.net/attachments/650460192009617433/665022187916492815/Compare.png"


def change_user(guildid: int, userid: int, changestyle: str, amount: SV):
    changestyle = changestyle.lower()
    if changestyle in ["add", "+", "a", "plus"]:
        changestyle = "add"
    if changestyle in ["subtract", "sub", "-", "minus"]:
        changestyle = "subtract"
    if changestyle in ["power", "exp", "pow", "exponent", "^", "**"]:
        changestyle = "power"
    if changestyle in ["multiply", "mult", "m", "x", "times", "*"]:
        changestyle = "multiply"
    if changestyle in ["divide", "d", "/", "div"]:
        changestyle = "divide"
    if changestyle in ["percent", "per", "perc", "%"]:
        changestyle = "percent"

    if changestyle not in ["add", "subtract", "multiply", "divide", "power", "percent"]:
        raise errors.ChangeMethodInvalidException(changestyle)

    amountSV = None
    amountVal = None
    newamount = None

    if changestyle in ["add", "subtract"]:
        amountSV = SV.parse(amount)
    elif changestyle in ["multiply", "divide", "power"]:
        amountVal = Decimal(amount)
        if amountVal == 1:
            raise errors.ValueIsOneException
        if amountVal == 0:
            raise errors.ValueIsZeroException
    elif changestyle in ["percent"]:
        amountVal = Decimal(amount)
        if amountVal == 0:
            raise errors.ValueIsZeroException

    userdata = userdb.load(guildid, userid)

    if changestyle == "add":
        newamount = userdata.height + amountSV
    elif changestyle == "subtract":
        newamount = userdata.height - amountSV
    elif changestyle == "multiply":
        newamount = userdata.height * amountVal
    elif changestyle == "divide":
        newamount = userdata.height / amountVal
    elif changestyle == "power":
        userdata = userdata ** amountVal
    elif changestyle == "percent":
        newamount = userdata.height * (amountVal / 100)

    if changestyle != "power":
        userdata.height = newamount

    userdb.save(userdata)


class EmbedToSend(TypedDict):
    embed: str


class StrToSend(TypedDict):
    content: str


def get_speedcompare(userdata1: User, userdata2: User, requesterID: int) -> EmbedToSend:
    _viewer, _viewed = minmax(userdata1, userdata2)

    # Use the new statbox
    viewer = StatBox.load(_viewer.stats).scale(_viewer.scale)
    viewed = StatBox.load(_viewed.stats).scale(_viewed.scale)

    if viewer['height'].value == 0 and viewed['height'].value == 0:
        multiplier = Decimal(1)
    else:
        multiplier = viewed['height'].value / viewer['height'].value

    footlabel = viewed['footname'].value
    hairlabel = viewed['hairname'].value

    requestertag = f"<@!{requesterID}>"
    embed = Embed(
        title=f"Speed/Distance Comparison of {viewed['nickname'].value} and {viewer['nickname'].value}",
        description=f"*Requested by {requestertag}*",
        color=colors.purple
    )
    embed.set_author(name=f"SizeBot {__version__}", icon_url=compareicon)
    embed.add_field(name=f"**{viewer['nickname'].value}** Speeds", value=(
        f"{emojis.walk} **Walk Speed:** {viewer['walkperhour'].value:,.3mu} per hour\n"
        f"{emojis.run} **Run Speed:** {viewer['runperhour'].value:,.3mu} per hour\n"
        f"{emojis.climb} **Climb Speed:** {viewer['climbperhour'].value:,.3mu} per hour\n"
        f"{emojis.crawl} **Crawl Speed:** {viewer['crawlperhour'].value:,.3mu} per hour\n"
        f"{emojis.swim} **Swim Speed:** {viewer['swimperhour'].value:,.3mu} per hour"), inline=False)
    embed.add_field(name="Height", value=(speedcalc(viewer, viewed['height'].value)), inline=True)
    embed.add_field(name=f"{footlabel} Length", value=(speedcalc(viewer, viewed['footlength'].value, foot = True)), inline=True)
    embed.add_field(name=f"{footlabel} Width", value=(speedcalc(viewer, viewed['footwidth'].value)), inline=True)
    embed.add_field(name="Toe Height", value=(speedcalc(viewer, viewed['toeheight'].value)), inline=True)
    embed.add_field(name="Shoeprint Depth", value=(speedcalc(viewer, viewed['shoeprintdepth'].value)), inline=True)
    embed.add_field(name="Pointer Finger Length", value=(speedcalc(viewer, viewed['pointerlength'].value)), inline=True)
    embed.add_field(name="Thumb Width", value=(speedcalc(viewer, viewed['thumbwidth'].value)), inline=True)
    embed.add_field(name="Nail Thickness", value=(speedcalc(viewer, viewed['nailthickness'].value)), inline=True)
    embed.add_field(name="Fingerprint Depth", value=(speedcalc(viewer, viewed['fingerprintdepth'].value)), inline=True)
    if viewed['hairlength'].value:
        embed.add_field(name=f"{hairlabel} Length", value=(speedcalc(viewed['hairlength'].value)), inline=True)
    if viewed['taillength'].value:
        embed.add_field(name="Tail Length", value=(speedcalc(viewer, viewed['taillength'].value)), inline=True)
    if viewed['earheight'].value:
        embed.add_field(name="Ear Height", value=(speedcalc(viewer, viewed['earheight'].value)), inline=True)
    embed.add_field(name=f"{hairlabel} Width", value=(speedcalc(viewer, viewed['hairwidth'].value)), inline=True)
    embed.add_field(name="Eye Width", value=(speedcalc(viewer, viewed['eyewidth'].value)), inline=True)
    embed.set_footer(text=(f"{viewed['nickname'].value} is {multiplier:,.3}x taller than {viewer['nickname'].value}."))

    return {"embed": embed}


def get_speedcompare_stat(userdata1: User, userdata2: User, key: str) -> EmbedToSend | None:
    _viewer, _viewed = minmax(userdata1, userdata2)

    # Use the new statbox
    viewer = StatBox.load(_viewer.stats).scale(_viewer.scale)
    viewed = StatBox.load(_viewed.stats).scale(_viewed.scale)

    try:
        mapped_key = statmap[key]
    except KeyError:
        return None

    stat = viewed[mapped_key]

    if stat.value is None:
        return None
    elif not isinstance(stat.value, SV):
        return None

    embed = Embed(
        title = f"To move the distance of {viewed['nickname'].value}'s {stat.title.lower()}, it would take {viewer['nickname'].value}...",
        description = speedcalc(viewer, stat.value, speed = True, include_relative = True, foot = mapped_key == "footlength"))
    return {"embed": embed}


def get_speeddistance(userdata: User, distance: SV) -> EmbedToSend | StrToSend:
    stats = StatBox.load(userdata.stats).scale(userdata.scale)
    if stats['height'].value > distance:
        distance_viewed = SV(distance * stats['viewscale'].value)
        msg = f"To {stats['nickname'].value}, {distance:,.3mu} appears to be **{distance_viewed:,.3mu}.**"
        return {"content": msg}
    multiplier = distance / stats['height'].value

    embed = Embed(
        title = f"{distance:,.3mu} to {stats['nickname'].value}",
        description = speedcalc(stats, distance, speed = True, include_relative = True))
    embed.set_footer(text = f"{distance:,.3mu} is {multiplier:,.3}x larger than {stats['nickname'].value}."),
    return {"embed": embed}


def get_speedtime(userdata: User, time: TV) -> EmbedToSend | StrToSend:
    stats = StatBox.load(userdata.stats).scale(userdata.scale)
    walkpersecond = SV(stats['walkperhour'].value / 3600)
    distance = SV(walkpersecond * time)
    return get_speeddistance(userdata, distance)


def get_compare(userdata1: User, userdata2: User, requesterID: int) -> EmbedToSend:
    stats1 = StatBox.load(userdata1.stats).scale(userdata1.scale)
    stats2 = StatBox.load(userdata2.stats).scale(userdata2.scale)
    small, big = sorted([stats1, stats2], key=lambda s: s['height'].value)
    if small['height'].value == 0 and big['height'].value == 0:
        # TODO: This feels awkward
        small_viewby_big = small.scale(1)
        big_viewby_small = big.scale(1)
        multiplier = Decimal(1)
    else:
        small_viewby_big = small.scale(big['viewscale'].value)
        big_viewby_small = big.scale(small['viewscale'].value)
        multiplier = big['height'].value / small['height'].value

    footname = join_unique([small['footname'].value, big['footname'].value], sep="/")
    hairname = join_unique([small['hairname'].value, big['hairname'].value], sep="/")

    viewangle = calc_view_angle(small['height'].value, big['height'].value)
    lookangle = abs(viewangle)
    lookdirection = "up" if viewangle >= 0 else "down"

    requestertag = f"<@!{requesterID}>"

    embed = Embed(
        title=f"Comparison of {big['nickname'].value} and {small['nickname'].value} {emojis.link}",
        description=f"*Requested by {requestertag}*",
        color=colors.purple,
        url = macrovision.get_url_from_statboxes([small, big])
    )
    if requesterID == big['id'].value:
        embed.color = colors.blue
    if requesterID == small['id'].value:
        embed.color = colors.red
    embed.set_author(name=f"SizeBot {__version__}", icon_url=compareicon)
    embed.add_field(name=f"{emojis.comparebigcenter} **{big['nickname'].value}**", value=(
        f"{emojis.blank}{emojis.blank} **Height:** {big['height'].value:,.3mu}\n"
        f"{emojis.blank}{emojis.blank} **Weight:** {big['weight'].value:,.3mu}\n"), inline=True)
    embed.add_field(name=f"{emojis.comparesmallcenter} **{small['nickname'].value}**", value=(
        f"{emojis.blank}{emojis.blank} **Height:** {small['height'].value:,.3mu}\n"
        f"{emojis.blank}{emojis.blank} **Weight:** {small['weight'].value:,.3mu}\n"), inline=True)
    embed.add_field(value=(
        f"{emojis.comparebig} represents how {emojis.comparebigcenter} **{big['nickname'].value}** looks to {emojis.comparesmallcenter} **{small['nickname'].value}**.\n"
        f"{emojis.comparesmall} represents how {emojis.comparesmallcenter} **{small['nickname'].value}** looks to {emojis.comparebigcenter} **{big['nickname'].value}**."), inline=False)
    embed.add_field(name="Height", value=(
        f"{emojis.comparebig}{big_viewby_small['height'].value:,.3mu}\n"
        f"{emojis.comparesmall}{small_viewby_big['height'].value:,.3mu}"), inline=True)
    embed.add_field(name="Weight", value=(
        f"{emojis.comparebig}{big_viewby_small['weight'].value:,.3mu}\n"
        f"{emojis.comparesmall}{small_viewby_big['weight'].value:,.3mu}"), inline=True)
    embed.add_field(name=f"{footname} Length", value=(
        f"{emojis.comparebig}{big_viewby_small['footlength'].value:,.3mu}\n({big_viewby_small['shoesize'].value})\n"
        f"{emojis.comparesmall}{small_viewby_big['footlength'].value:,.3mu}\n({small_viewby_big['shoesize'].value})"), inline=True)
    embed.add_field(name=f"{footname} Width", value=(
        f"{emojis.comparebig}{big_viewby_small['footwidth'].value:,.3mu}\n"
        f"{emojis.comparesmall}{small_viewby_big['footwidth'].value:,.3mu}"), inline=True)
    embed.add_field(name="Toe Height", value=(
        f"{emojis.comparebig}{big_viewby_small['toeheight'].value:,.3mu}\n"
        f"{emojis.comparesmall}{small_viewby_big['toeheight'].value:,.3mu}"), inline=True)
    embed.add_field(name="Shoeprint Depth", value=(
        f"{emojis.comparebig}{big_viewby_small['shoeprintdepth'].value:,.3mu}\n"
        f"{emojis.comparesmall}{small_viewby_big['shoeprintdepth'].value:,.3mu}"), inline=True)
    embed.add_field(name="Pointer Finger Length", value=(
        f"{emojis.comparebig}{big_viewby_small['pointerlength'].value:,.3mu}\n"
        f"{emojis.comparesmall}{small_viewby_big['pointerlength'].value:,.3mu}"), inline=True)
    embed.add_field(name="Thumb Width", value=(
        f"{emojis.comparebig}{big_viewby_small['thumbwidth'].value:,.3mu}\n"
        f"{emojis.comparesmall}{small_viewby_big['thumbwidth'].value:,.3mu}"), inline=True)
    embed.add_field(name="Nail Thickness", value=(
        f"{emojis.comparebig}{big_viewby_small['nailthickness'].value:,.3mu}\n"
        f"{emojis.comparesmall}{small_viewby_big['nailthickness'].value:,.3mu}"), inline=True)
    embed.add_field(name="Fingerprint Depth", value=(
        f"{emojis.comparebig}{big_viewby_small['fingerprintdepth'].value:,.3mu}\n"
        f"{emojis.comparesmall}{small_viewby_big['fingerprintdepth'].value:,.3mu}"), inline=True)
    if big_viewby_small['hairlength'].value or small_viewby_big['hairlength'].value:
        hairfield = ""
        if big_viewby_small['hairlength'].value:
            hairfield += f"{emojis.comparebig}{big_viewby_small['hairlength'].value:,.3mu}\n"
        if small_viewby_big['hairlength'].value:
            hairfield += f"{emojis.comparesmall}{small_viewby_big['hairlength'].value:,.3mu}\n"
        hairfield = hairfield.strip()
        embed.add_field(name=f"{hairname} Length", value=hairfield, inline=True)
    if big_viewby_small['taillength'].value or small_viewby_big['taillength'].value:
        tailfield = ""
        if big_viewby_small['taillength'].value:
            tailfield += f"{emojis.comparebig}{big_viewby_small['taillength'].value:,.3mu}\n"
        if small_viewby_big['taillength'].value:
            tailfield += f"{emojis.comparesmall}{small_viewby_big['taillength'].value:,.3mu}\n"
        tailfield = tailfield.strip()
        embed.add_field(name="Tail Length", value=tailfield, inline=True)
    if big_viewby_small['earheight'].value or small_viewby_big['earheight'].value:
        earfield = ""
        if big_viewby_small['earheight'].value:
            earfield += f"{emojis.comparebig}{big_viewby_small['earheight'].value:,.3mu}\n"
        if small_viewby_big['earheight'].value:
            earfield += f"{emojis.comparesmall}{small_viewby_big['earheight'].value:,.3mu}\n"
        earfield = earfield.strip()
        embed.add_field(name="Ear Height", value=earfield, inline=True)
    embed.add_field(name=f"{hairname} Width", value=(
        f"{emojis.comparebig}{big_viewby_small['hairwidth'].value:,.3mu}\n"
        f"{emojis.comparesmall}{small_viewby_big['hairwidth'].value:,.3mu}"), inline=True)
    embed.add_field(name="Eye Width", value=(
        f"{emojis.comparebig}{big_viewby_small['eyewidth'].value:,.3mu}\n"
        f"{emojis.comparesmall}{small_viewby_big['eyewidth'].value:,.3mu}"), inline=True)
    embed.add_field(name="Jump Height", value=(
        f"{emojis.comparebig}{big_viewby_small['jumpheight'].value:,.3mu}\n"
        f"{emojis.comparesmall}{small_viewby_big['jumpheight'].value:,.3mu}"), inline=True)
    embed.add_field(name="Lift/Carry Strength", value=(
        f"{emojis.comparebig}{big_viewby_small['liftstrength'].value:,.3mu}\n"
        f"{emojis.comparesmall}{small_viewby_big['liftstrength'].value:,.3mu}"), inline=True)
    embed.add_field(name=f"{emojis.comparebig} Speeds", value=big_viewby_small['simplespeeds+'].body, inline=False)
    embed.add_field(name=f"{emojis.comparesmall} Speeds", value=small_viewby_big['simplespeeds+'].body, inline=False)
    embed.set_footer(text=(
        f"{small['nickname'].value} would have to look {lookdirection} {lookangle:.0f}° to look at {big['nickname'].value}'s face.\n"
        f"{big['nickname'].value} is {multiplier:,.3}x taller than {small['nickname'].value}.\n"
        f"{big['nickname'].value} would need {small_viewby_big['visibility'].value} to see {small['nickname'].value}."))

    return {"embed": embed}


def get_compare_simple(userdata1: User, userdata2: User, requesterID: int) -> EmbedToSend:
    stats1 = StatBox.load(userdata1.stats).scale(userdata1.scale)
    stats2 = StatBox.load(userdata2.stats).scale(userdata2.scale)
    small, big = sorted([stats1, stats2], key=lambda s: s['height'].value)
    if small['height'].value == 0 and big['height'].value == 0:
        # TODO: This feels awkward
        small_viewby_big = small.scale(1)
        big_viewby_small = big.scale(1)
        multiplier = Decimal(1)
    else:
        small_viewby_big = small.scale(big['viewscale'].value)
        big_viewby_small = big.scale(small['viewscale'].value)
        multiplier = big['height'].value / small['height'].value

    viewangle = calc_view_angle(small['height'].value, big['height'].value)
    lookangle = abs(viewangle)
    lookdirection = "up" if viewangle >= 0 else "down"

    requestertag = f"<@!{requesterID}>"

    embed = Embed(
        title=f"Comparison of {big['nickname'].value} and {small['nickname'].value} {emojis.link}",
        description=f"*Requested by {requestertag}*",
        color=colors.purple,
        url = macrovision.get_url_from_statboxes([small, big])
    )
    if requesterID == big['id'].value:
        embed.color = colors.blue
    if requesterID == small['id'].value:
        embed.color = colors.red
    embed.set_author(name=f"SizeBot {__version__}", icon_url=compareicon)
    embed.add_field(name=f"{emojis.comparebigcenter} **{big['nickname'].value}**", value=(
        f"{emojis.blank}{emojis.blank} **Height:** {big['height'].value:,.3mu}\n"
        f"{emojis.blank}{emojis.blank} **Weight:** {big['weight'].value:,.3mu}\n"), inline=True)
    embed.add_field(name=f"{emojis.comparesmallcenter} **{small['nickname'].value}**", value=(
        f"{emojis.blank}{emojis.blank} **Height:** {small['height'].value:,.3mu}\n"
        f"{emojis.blank}{emojis.blank} **Weight:** {small['weight'].value:,.3mu}\n"), inline=True)
    embed.add_field(value=(
        f"{emojis.comparebig} represents how {emojis.comparebigcenter} **{big['nickname'].value}** looks to {emojis.comparesmallcenter} **{small['nickname'].value}**.\n"
        f"{emojis.comparesmall} represents how {emojis.comparesmallcenter} **{small['nickname'].value}** looks to {emojis.comparebigcenter} **{big['nickname'].value}**."), inline=False)
    embed.add_field(name="Height", value=(
        f"{emojis.comparebig}{big_viewby_small['height'].value:,.3mu}\n"
        f"{emojis.comparesmall}{small_viewby_big['height'].value:,.3mu}"), inline=True)
    embed.add_field(name="Weight", value=(
        f"{emojis.comparebig}{big_viewby_small['weight'].value:,.3mu}\n"
        f"{emojis.comparesmall}{small_viewby_big['weight'].value:,.3mu}"), inline=True)
    embed.set_footer(text=(
        f"{small['nickname'].value} would have to look {lookdirection} {lookangle:.0f}° to look at {big['nickname'].value}'s face.\n"
        f"{big['nickname'].value} is {multiplier:,.3}x taller than {small['nickname'].value}.\n"
        f"{big['nickname'].value} would need {small_viewby_big['visibility'].value} to see {small['nickname'].value}."))

    return {"embed": embed}


def get_compare_stat(userdata1: User, userdata2: User, key: str) -> StrToSend | None:
    stats1 = StatBox.load(userdata1.stats).scale(userdata1.scale)
    stats2 = StatBox.load(userdata2.stats).scale(userdata2.scale)
    small, big = sorted([stats1, stats2], key=lambda s: s['height'].value)
    if small['height'].value == 0 and big['height'].value == 0:
        # TODO: This feels awkward
        small_viewby_big = small.scale(1)
        big_viewby_small = big.scale(1)
    else:
        small_viewby_big = small.scale(big['viewscale'].value)
        big_viewby_small = big.scale(small['viewscale'].value)

    try:
        mapped_key = statmap[key]
    except KeyError:
        return None

    smallstat = small_viewby_big[mapped_key]
    bigstat = big_viewby_small[mapped_key]

    bigstattext = bigstat.body if bigstat.value is not None else f"{big['nickname'].value} doesn't have that stat."
    smallstattext = smallstat.body if smallstat.value is not None else f"{small['nickname'].value} doesn't have that stat."

    msg = (
        f"Comparing `{key}` between {emojis.comparebigcenter}**{big['nickname'].value}** and **{emojis.comparesmallcenter}{small['nickname'].value}**:\n"
        f"{emojis.comparebig}{bigstattext}\n"
        f"{emojis.comparesmall}{smallstattext}")

    return {"content": msg}


def get_stats(userdata: User, requesterID: int) -> EmbedToSend:
    stats = StatBox.load(userdata.stats).scale(userdata.scale)
    avgstats = StatBox.load_average()
    avgstatsview = avgstats.scale(stats['viewscale'].value)

    viewangle = calc_view_angle(stats['height'].value, avgstats['height'].value)
    avglookdirection = "up" if viewangle >= 0 else "down"
    avglookangle = abs(viewangle)
    requestertag = f"<@!{requesterID}>"
    embed = Embed(
        title=f"Stats for {stats['nickname'].value}",
        description=f"*Requested by {requestertag}*",
        color=colors.cyan)
    embed.set_author(name=f"SizeBot {__version__}")

    for stat in stats:
        if stat.is_shown:
            embed.add_field(**stat.embed)

    embed.set_footer(text=f"An average person would look {avgstatsview['height'].value:,.3mu}, and weigh {avgstatsview['weight'].value:,.3mu} to you. You'd have to look {avglookdirection} {avglookangle:.0f}° to see them.")

    return {"embed": embed}


def get_stats_bytag(userdata: User, tag: str, requesterID: int) -> EmbedToSend:
    stats = StatBox.load(userdata.stats).scale(userdata.scale)
    requestertag = f"<@!{requesterID}>"
    embed = Embed(
        title=f"Stats for {stats['nickname'].value} tagged `{tag}`",
        description=f"*Requested by {requestertag}*",
        color=colors.cyan)
    embed.set_author(name=f"SizeBot {__version__}")
    for stat in stats:
        if tag in stat.tags:
            embed.add_field(**stat.embed)

    return {"embed": embed}


def get_stat(userdata: User, key: str) -> StrToSend | None:
    stats = StatBox.load(userdata.stats).scale(userdata.scale)
    try:
        mapped_key = statmap[key]
    except KeyError:
        return None
    msg = stats[mapped_key].string
    return {"content": msg}


def get_basestats(userdata: User, requesterID = None) -> EmbedToSend:
    basestats = StatBox.load(userdata.stats)
    requestertag = f"<@!{requesterID}>"
    embed = Embed(title=f"Base Stats for {basestats['nickname'].value}",
                  description=f"*Requested by {requestertag}*",
                  color=colors.cyan)
    embed.set_author(name=f"SizeBot {__version__}")

    for stat in basestats:
        if stat.is_shown:
            embed.add_field(**stat.embed)

    # REMOVED: unitsystem, furcheck, pawcheck, tailcheck, macrovision_model, macrovision_view
    return {"embed": embed}


def get_settings(userdata: User, requesterID = None) -> EmbedToSend:
    basestats = StatBox.load(userdata.stats)
    requestertag = f"<@!{requesterID}>"
    embed = Embed(title=f"Settings for {basestats['nickname'].value}",
                  description=f"*Requested by {requestertag}*",
                  color=colors.cyan)
    embed.set_author(name=f"SizeBot {__version__}")

    for stat in basestats:
        if stat.definition.userkey is not None:
            if stat.is_setbyuser:
                embed.add_field(**stat.embed)
            else:
                embed.add_field(
                    name=stat.title,
                    value="**NOT SET**",
                    inline=stat.definition.inline
                )

    return {"embed": embed}
