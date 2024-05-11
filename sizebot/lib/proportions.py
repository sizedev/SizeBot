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
    small, big, _, _, multiplier = _get_compare_statboxes(userdata1, userdata2)

    embed = _create_compare_embed(
        f"Speed/Distance Comparison of {big['nickname'].value} and {small['nickname'].value}",
        requesterID)

    embed.add_field(name=f"**{small["nickname"].value}** Speeds", value=small.stats_by_key["simplespeeds+"].body, inline=False)

    embed.add_field(name="Height", value=speedcalc(small, big["height"].value, include_relative = True), inline=True)  # hardcode height because it's weird
    embed.add_field(name="Foot Length", value=speedcalc(small, big["footlength"].value, include_relative = True, foot = True), inline=True)  # hardcode height because it's weird

    for stat in big.stats:
        if stat.is_shown and stat.is_set and isinstance(stat.value, SV) and stat.key != "terminalvelocity":
            embed.add_field(name = stat.title, value=(speedcalc(small, stat.value, include_relative = True, foot = stat.key == "footlength")))

    embed.set_footer(text=(f"{big['nickname'].value} is {multiplier:,.3}x taller than {small['nickname'].value}."))

    return {"embed": embed}


def get_speedcompare_stat(userdata1: User, userdata2: User, key: str) -> EmbedToSend | None:
    small, big, _, _, _ = _get_compare_statboxes(userdata1, userdata2)
    mapped_key = _get_mapped_stat(key)
    if mapped_key is None:
        return None
    stat = big[mapped_key]
    if not isinstance(stat.value, SV):
        return None

    embed = Embed(
        title = f"To move the distance of {big['nickname'].value}'s {stat.title.lower()}, it would take {small['nickname'].value}...",
        description = speedcalc(small, stat.value, speed = True, include_relative = True, foot = mapped_key == "footlength")
    )
    return {"embed": embed}


def get_speeddistance(userdata: User, distance: SV) -> EmbedToSend | StrToSend:
    stats = StatBox.load(userdata.stats).scale(userdata.scale)

    distance_viewed = SV(distance * stats['viewscale'].value)
    if stats['height'].value > distance:
        msg = f"To {stats['nickname'].value}, {distance:,.3mu} appears to be **{distance_viewed:,.3mu}.**"
        return {"content": msg}
    multiplier = distance / stats['height'].value

    embed = Embed(
        title = f"{distance:,.3mu} to {stats['nickname'].value}",
        description = speedcalc(stats, distance, speed = True, include_relative = True)
    )
    embed.set_footer(text = f"{distance:,.3mu} is {multiplier:,.3}x larger than {stats['nickname'].value}. It looks to be about {format_close_object_smart(distance_viewed)}."),
    return {"embed": embed}


def get_speedtime(userdata: User, time: TV) -> EmbedToSend | StrToSend:
    stats = StatBox.load(userdata.stats).scale(userdata.scale)

    walkpersecond = SV(stats['walkperhour'].value / 3600)
    distance = SV(walkpersecond * time)
    return get_speeddistance(userdata, distance)


def get_compare(userdata1: User, userdata2: User, requesterID: int) -> EmbedToSend:
    small, big, small_viewby_big, big_viewby_small, _ = _get_compare_statboxes(userdata1, userdata2)

    embed = _create_compare_embed(
        f"Comparison of {big['nickname'].value} and {small['nickname'].value} {emojis.link}",
        requesterID, small, big)

    embed.add_field(value=(
        f"{emojis.comparebig} represents how {emojis.comparebigcenter} **{big['nickname'].value}** looks to {emojis.comparesmallcenter} **{small['nickname'].value}**.\n"
        f"{emojis.comparesmall} represents how {emojis.comparesmallcenter} **{small['nickname'].value}** looks to {emojis.comparebigcenter} **{big['nickname'].value}**."), inline=False)

    for small_stat, big_stat in zip(small_viewby_big, big_viewby_small):
        if (small_stat.is_shown or big_stat.is_shown) and (small_stat.is_set or big_stat.is_set):
            embed.add_field(**_create_compare_field(small, big, small_stat, big_stat))

    return {"embed": embed}


def get_compare_simple(userdata1: User, userdata2: User, requesterID: int) -> EmbedToSend:
    small, big, small_viewby_big, big_viewby_small, multiplier = _get_compare_statboxes(userdata1, userdata2)
    lookangle, lookdirection = _calc_view(small['height'].value, big['height'].value)

    embed = _create_compare_embed(
        f"Comparison of {big['nickname'].value} and {small['nickname'].value} {emojis.link}",
        requesterID, small, big)

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
    small, big, small_viewby_big, big_viewby_small, multiplier = _get_compare_statboxes(userdata1, userdata2)
    lookangle, lookdirection = _calc_view(small['height'].value, big['height'].value)

    embed = _create_compare_embed(
        f"Comparison of {big['nickname'].value} and {small['nickname'].value} {emojis.link} of stats tagged `{tag}`",
        requesterID, small, big)

    embed.add_field(value=(
        f"{emojis.comparebig} represents how {emojis.comparebigcenter} **{big['nickname'].value}** looks to {emojis.comparesmallcenter} **{small['nickname'].value}**.\n"
        f"{emojis.comparesmall} represents how {emojis.comparesmallcenter} **{small['nickname'].value}** looks to {emojis.comparebigcenter} **{big['nickname'].value}**."), inline=False)

    # TODO: Zip only works if we can guarantee each statbox has the same stats in the same order.
    for small_stat, big_stat in zip(small_viewby_big, big_viewby_small):
        if tag in small_stat.tags and (small_stat.body or big_stat.body):
            embed.add_field(**_create_compare_field(small, big, small_stat, big_stat))

    embed.set_footer(text=(
        f"{small['nickname'].value} would have to look {lookdirection} {lookangle:.0f}° to look at {big['nickname'].value}'s face.\n"
        f"{big['nickname'].value} is {multiplier:,.3}x taller than {small['nickname'].value}.\n"
        f"{big['nickname'].value} would need {small_viewby_big['visibility'].value} to see {small['nickname'].value}."))

    return {"embed": embed}


def get_compare_stat(userdata1: User, userdata2: User, key: str) -> StrToSend | None:
    small, big, small_viewby_big, big_viewby_small, _ = _get_compare_statboxes(userdata1, userdata2)
    mapped_key = _get_mapped_stat(key)
    if mapped_key is None:
        return None
    small_stat = small_viewby_big[mapped_key]
    big_stat = big_viewby_small[mapped_key]

    body = _create_compare_body(small, big, small_stat, big_stat)

    msg = (
        f"Comparing `{key}` between {emojis.comparebigcenter}**{big['nickname'].value}** and **{emojis.comparesmallcenter}{small['nickname'].value}**:"
        f"\n{body}"
    )

    return {"content": msg}


def get_stats(userdata: User, requesterID: int) -> EmbedToSend:
    viewer = StatBox.load(userdata.stats).scale(userdata.scale)
    avg = StatBox.load_average()
    avg_viewedby_viewer = avg.scale(viewer['viewscale'].value)
    lookangle, lookdirection = _calc_view(viewer['height'].value, avg['height'].value)

    embed = _create_embed(f"Stats for {viewer['nickname'].value}", requesterID)

    for stat in viewer:
        if stat.is_shown:
            embed.add_field(**stat.embed)

    embed.set_footer(text=f"An average person would look {avg_viewedby_viewer['height'].value:,.3mu}, and weigh {avg_viewedby_viewer['weight'].value:,.3mu} to you. You'd have to look {lookdirection} {lookangle:.0f}° to see them.")

    return {"embed": embed}


def get_stats_bytag(userdata: User, tag: str, requesterID: int) -> EmbedToSend:
    stats = StatBox.load(userdata.stats).scale(userdata.scale)

    embed = _create_embed(f"Stats for {stats['nickname'].value} tagged `{tag}`", requesterID)

    for stat in stats:
        if tag in stat.tags:
            embed.add_field(**stat.embed)

    return {"embed": embed}


def get_stat(userdata: User, key: str) -> StrToSend | None:
    mapped_key = _get_mapped_stat(key)
    if mapped_key is None:
        return None
    stats = StatBox.load(userdata.stats).scale(userdata.scale)
    stat = stats[mapped_key]

    msg = f"{stat.string}"
    if isinstance(stat.value, (SV, WV)):
        msg += f"\n*That\'s about {format_close_object_smart(stat.value)}.*"
    return {"content": msg}


def get_basestats(userdata: User, requesterID: int) -> EmbedToSend:
    basestats = StatBox.load(userdata.stats)

    embed = _create_embed(f"Base Stats for {basestats['nickname'].value}", requesterID)

    for stat in basestats:
        if stat.is_shown:
            embed.add_field(**stat.embed)

    # REMOVED: unitsystem, furcheck, pawcheck, tailcheck, macrovision_model, macrovision_view
    return {"embed": embed}


def get_settings(userdata: User, requesterID: int) -> EmbedToSend:
    basestats = StatBox.load(userdata.stats)

    embed = _create_embed(f"Settings for {basestats['nickname'].value}", requesterID)

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


def get_keypoints_embed(userdata: User, requesterID: int) -> EmbedToSend:
    stats = StatBox.load(userdata.stats).scale(userdata.scale)

    embed = _create_embed(f"Keypoints for {stats['nickname'].value}", requesterID)

    for stat in stats:
        if "keypoint" in stat.tags:
            lookslike = format_close_object_smart(stat.value)
            embed.add_field(name = stat.title, value = f"{stat.body}\n*~{lookslike}*")

    return {"embed": embed}


def _create_compare_embed(title: str, requesterID: int, small: StatBox, big: StatBox):
    requestertag = f"<@!{requesterID}>"
    if small is not None and big is not None:
        color = _get_compare_color(requesterID, small, big)
        url = macrovision.get_url_from_statboxes([small, big])
    else:
        color = colors.purple
        url = None
    embed = Embed(title=title,
                  description=f"*Requested by {requestertag}*",
                  color=color,
                  url=url)
    embed.set_author(name=f"SizeBot {__version__}", icon_url=compareicon)
    return embed


def _create_embed(title: str, requesterID: int) -> Embed:
    requestertag = f"<@!{requesterID}>"
    embed = Embed(title=title,
                  description=f"*Requested by {requestertag}*")
    embed.set_author(name=f"SizeBot {__version__}")
    return embed


def _create_compare_field(small: StatBox, big: StatBox, small_stat: Stat, big_stat: Stat) -> EmbedField:
    embedfield = {
        "name": small_stat.title,
        "value": _create_compare_body(small, big, small_stat, big_stat),
        "inline": small_stat.definition.inline
    }

    return embedfield


def _create_compare_body(small: StatBox, big: StatBox, small_stat: Stat, big_stat: Stat) -> str:
    return (
        f"{emojis.comparebig}{_create_stat_body(big, big_stat)}\n"
        f"{emojis.comparesmall}{_create_stat_body(small, small_stat)}"
    )


def _create_stat_body(stats: StatBox, stat: Stat) -> str:
    if not stat.is_set:
        return f"{stats['nickname'].value} doesn't have that stat."
    return stat.body


def _get_compare_color(requesterID: int, small: StatBox, big: StatBox):
    if requesterID == big['id'].value:
        return colors.blue
    if requesterID == small['id'].value:
        return colors.red
    return colors.purple


def _get_mapped_stat(key: str) -> str | None:
    try:
        mapped_key = statmap[key]
    except KeyError:
        return None
    return mapped_key


def _get_compare_statboxes(userdata1: User, userdata2: User) -> tuple[StatBox, StatBox, StatBox, StatBox, Decimal]:
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
    return small, big, small_viewby_big, big_viewby_small, multiplier


def _calc_view(viewer: SV, viewee: SV) -> tuple[Decimal, str]:
    viewangle = calc_view_angle(viewer, viewee)
    lookangle = abs(viewangle)
    lookdirection = "up" if viewangle >= 0 else "down"
    return lookangle, lookdirection
