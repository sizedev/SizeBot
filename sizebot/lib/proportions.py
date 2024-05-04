from __future__ import annotations
from typing import TypedDict

import logging

from discord import Embed

from sizebot import __version__
from sizebot.lib import macrovision
from sizebot.lib.constants import colors, emojis
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.objs import format_close_object_smart
from sizebot.lib.speed import speedcalc
from sizebot.lib.units import SV, TV, WV
from sizebot.lib.userdb import User
from sizebot.lib.utils import minmax
from sizebot.lib.stats import Stat, calc_view_angle, statmap, StatBox

logger = logging.getLogger("sizebot")

compareicon = "https://media.discordapp.net/attachments/650460192009617433/665022187916492815/Compare.png"


class EmbedToSend(TypedDict):
    embed: str


class StrToSend(TypedDict):
    content: str


class EmbedField(TypedDict):
    name: str
    value: str
    inline: bool


def get_speedcompare(userdata1: User, userdata2: User, requesterID: int) -> EmbedToSend:
    _viewer, _viewed = minmax(userdata1, userdata2)

    # Use the new statbox
    viewer = StatBox.load(_viewer.stats).scale(_viewer.scale)
    viewed = StatBox.load(_viewed.stats).scale(_viewed.scale)

    if viewer['height'].value == 0 and viewed['height'].value == 0:
        multiplier = Decimal(1)
    else:
        multiplier = viewed['height'].value / viewer['height'].value

    requestertag = f"<@!{requesterID}>"
    embed = Embed(
        title=f"Speed/Distance Comparison of {viewed['nickname'].value} and {viewer['nickname'].value}",
        description=f"*Requested by {requestertag}*",
        color=colors.purple
    )
    embed.set_author(name=f"SizeBot {__version__}", icon_url=compareicon)

    embed.add_field(name=f"**{viewer["nickname"].value}** Speeds", value=viewer.stats_by_key["simplespeeds+"].body, inline=False)

    embed.add_field(name="Height", value=speedcalc(viewer, viewed["height"].value, include_relative = True), inline=True)  # hardcode height because it's weird
    embed.add_field(name="Foot Length", value=speedcalc(viewer, viewed["footlength"].value, include_relative = True, foot = True), inline=True)  # hardcode height because it's weird

    for stat in viewed.stats:
        if stat.is_shown and stat.is_set and isinstance(stat.value, SV) and stat.key != "terminalvelocity":
            embed.add_field(name = stat.title, value=(speedcalc(viewer, stat.value, include_relative = True, foot = stat.key == "footlength")))

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
    embed.set_footer(text = f"{distance:,.3mu} is {multiplier:,.3}x larger than {stats['nickname'].value}. It looks to be about {format_close_object_smart(distance_viewed)}."),
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
    else:
        small_viewby_big = small.scale(big['viewscale'].value)
        big_viewby_small = big.scale(small['viewscale'].value)

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
    embed.add_field(value=(
        f"{emojis.comparebig} represents how {emojis.comparebigcenter} **{big['nickname'].value}** looks to {emojis.comparesmallcenter} **{small['nickname'].value}**.\n"
        f"{emojis.comparesmall} represents how {emojis.comparesmallcenter} **{small['nickname'].value}** looks to {emojis.comparebigcenter} **{big['nickname'].value}**."), inline=False)

    for small_stat, big_stat in zip(small_viewby_big, big_viewby_small):
        if (small_stat.is_shown or big_stat.is_shown) and (small_stat.is_set or big_stat.is_set):
            embed.add_field(**get_compare_field(small, big, small_stat, big_stat))

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


def get_compare_bytag(userdata1: User, userdata2: User, tag: str, requesterID: int) -> EmbedToSend:
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
        title=f"Comparison of {big['nickname'].value} and {small['nickname'].value} {emojis.link} of stats tagged `{tag}`",
        description=f"*Requested by {requestertag}*",
        color=colors.purple,
        url = macrovision.get_url_from_statboxes([small, big])
    )
    if requesterID == big['id'].value:
        embed.color = colors.blue
    if requesterID == small['id'].value:
        embed.color = colors.red
    embed.set_author(name=f"SizeBot {__version__}", icon_url=compareicon)
    embed.add_field(value=(
        f"{emojis.comparebig} represents how {emojis.comparebigcenter} **{big['nickname'].value}** looks to {emojis.comparesmallcenter} **{small['nickname'].value}**.\n"
        f"{emojis.comparesmall} represents how {emojis.comparesmallcenter} **{small['nickname'].value}** looks to {emojis.comparebigcenter} **{big['nickname'].value}**."), inline=False)

    # TODO: Zip only works if we can guarantee each statbox has the same stats in the same order.
    for small_stat, big_stat in zip(small_viewby_big, big_viewby_small):
        if tag in small_stat.tags and (small_stat.body or big_stat.body):
            embed.add_field(**get_compare_field(small, big, small_stat, big_stat))

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

    small_stat = small_viewby_big[mapped_key]
    big_stat = big_viewby_small[mapped_key]

    body = get_compare_body(small, big, small_stat, big_stat)
    if body is None:
        return None

    msg = (
        f"Comparing `{key}` between {emojis.comparebigcenter}**{big['nickname'].value}** and **{emojis.comparesmallcenter}{small['nickname'].value}**:"
        f"\n{body}"
    )

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
    stat = stats[mapped_key]
    msg = f"{stat.string}"
    if isinstance(stat.value, (SV, WV)):
        msg += f"\n*That\'s about {format_close_object_smart(stat.value)}.*"
    return {"content": msg}


def get_basestats(userdata: User, requesterID: int = None) -> EmbedToSend:
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


def get_settings(userdata: User, requesterID: int = None) -> EmbedToSend:
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


def get_keypoints_embed(userdata: User, requesterID: int = None) -> EmbedToSend:
    stats = StatBox.load(userdata.stats).scale(userdata.scale)

    requestertag = f"<@!{requesterID}>"
    embed = Embed(title=f"Keypoints for {stats['nickname'].value}",
                  description=f"*Requested by {requestertag}*",
                  color=colors.cyan)
    embed.set_author(name=f"SizeBot {__version__}")

    for stat in stats:
        if "keypoint" in stat.tags:
            lookslike = format_close_object_smart(stat.value)
            embed.add_field(name = stat.title, value = f"{stat.body}\n*~{lookslike}*")

    return {"embed": embed}


def get_compare_field(small: StatBox, big: StatBox, small_stat: Stat, big_stat: Stat) -> EmbedField:
    embedfield = {
        "name": small_stat.title,
        "value": get_compare_body(small, big, small_stat, big_stat),
        "inline": small_stat.definition.inline
    }

    return embedfield


def get_compare_body(small: StatBox, big: StatBox, small_stat: Stat, big_stat: Stat) -> str:
    return (
        f"{emojis.comparebig}{get_stat_body(big, big_stat)}\n"
        f"{emojis.comparesmall}{get_stat_body(small, small_stat)}"
    )


def get_stat_body(stats: StatBox, stat: Stat) -> str:
    if not stat.is_set:
        return f"{stats['nickname'].value} doesn't have that stat."
    return stat.body
