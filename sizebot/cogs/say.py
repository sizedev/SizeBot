import re
import logging
from sizebot.lib.versioning import release_on
import typing

import discord
from discord.ext import commands

from sizebot.lib import userdb
from sizebot.lib.constants import emojis
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.units import SV
from sizebot.lib.errors import UserNotFoundException


logger = logging.getLogger("sizebot")

smol_letters = str.maketrans({
    '0': '⁰',
    '1': '¹',
    '2': '²',
    '3': '³',
    '4': '⁴',
    '5': '⁵',
    '6': '⁶',
    '7': '⁷',
    '8': '⁸',
    '9': '⁹',
    '+': '⁺',
    '-': '⁻',
    'a': 'ᵃ',
    'b': 'ᵇ',
    'c': 'ᶜ',
    'd': 'ᵈ',
    'e': 'ᵉ',
    'f': 'ᶠ',
    'g': 'ᵍ',
    'h': 'ʰ',
    'i': 'ⁱ',
    'j': 'ʲ',
    'k': 'ᵏ',
    'l': 'ˡ',
    'm': 'ᵐ',
    'n': 'ⁿ',
    'o': 'ᵒ',
    'p': 'ᵖ',
    'q': 'ᑫ',
    'r': 'ʳ',
    's': 'ˢ',
    't': 'ᵗ',
    'u': 'ᵘ',
    'v': 'ᵛ',
    'w': 'ʷ',
    'x': 'ˣ',
    'y': 'ʸ',
    'z': 'ᶻ',
    'A': 'ᴬ',
    'B': 'ᴮ',
    'C': 'ᶜ',
    'D': 'ᴰ',
    'E': 'ᴱ',
    'F': 'ᶠ',
    'G': 'ᴳ',
    'H': 'ᴴ',
    'I': 'ᴵ',
    'J': 'ᴶ',
    'K': 'ᴷ',
    'L': 'ᴸ',
    'M': 'ᴹ',
    'N': 'ᴺ',
    'O': 'ᴼ',
    'P': 'ᴾ',
    'Q': 'ᵠ',
    'R': 'ᴿ',
    'S': 'ˢ',
    'T': 'ᵀ',
    'U': 'ᵁ',
    'V': 'ⱽ',
    'W': 'ᵂ',
    'X': 'ˣ',
    'Y': 'ʸ',
    'Z': 'ᶻ'
})

small_caps = str.maketrans({
    'a': 'ᴀ',
    'b': 'ʙ',
    'c': 'ᴄ',
    'd': 'ᴅ',
    'e': 'ᴇ',
    'f': 'ꜰ',
    'g': 'ɢ',
    'h': 'ʜ',
    'i': 'ɪ',
    'j': 'ᴊ',
    'k': 'ᴋ',
    'l': 'ʟ',
    'm': 'ᴍ',
    'n': 'ɴ',
    'o': 'ᴏ',
    'p': 'ᴘ',
    'q': 'ǫ',
    'r': 'ʀ',
    's': 's',
    't': 'ᴛ',
    'u': 'ᴜ',
    'v': 'ᴠ',
    'w': 'ᴡ',
    'x': 'x',
    'y': 'ʏ',
    'z': 'ᴢ'
})

giant_letters = str.maketrans({
    'a': ':regional_indicator_a:',
    'b': ':regional_indicator_b:',
    'c': ':regional_indicator_c:',
    'd': ':regional_indicator_d:',
    'e': ':regional_indicator_e:',
    'f': ':regional_indicator_f:',
    'g': ':regional_indicator_g:',
    'h': ':regional_indicator_h:',
    'i': ':regional_indicator_i:',
    'j': ':regional_indicator_j:',
    'k': ':regional_indicator_k:',
    'l': ':regional_indicator_l:',
    'm': ':regional_indicator_m:',
    'n': ':regional_indicator_n:',
    'o': ':regional_indicator_o:',
    'p': ':regional_indicator_p:',
    'q': ':regional_indicator_q:',
    'r': ':regional_indicator_r:',
    's': ':regional_indicator_s:',
    't': ':regional_indicator_t:',
    'u': ':regional_indicator_u:',
    'v': ':regional_indicator_v:',
    'w': ':regional_indicator_w:',
    'x': ':regional_indicator_x:',
    'y': ':regional_indicator_y:',
    'z': ':regional_indicator_z:',
    'A': ':regional_indicator_a:',
    'B': ':regional_indicator_b:',
    'C': ':regional_indicator_c:',
    'D': ':regional_indicator_d:',
    'E': ':regional_indicator_e:',
    'F': ':regional_indicator_f:',
    'G': ':regional_indicator_g:',
    'H': ':regional_indicator_h:',
    'I': ':regional_indicator_i:',
    'J': ':regional_indicator_j:',
    'K': ':regional_indicator_k:',
    'L': ':regional_indicator_l:',
    'M': ':regional_indicator_m:',
    'N': ':regional_indicator_n:',
    'O': ':regional_indicator_o:',
    'P': ':regional_indicator_p:',
    'Q': ':regional_indicator_q:',
    'R': ':regional_indicator_r:',
    'S': ':regional_indicator_s:',
    'T': ':regional_indicator_t:',
    'U': ':regional_indicator_u:',
    'V': ':regional_indicator_v:',
    'W': ':regional_indicator_w:',
    'X': ':regional_indicator_x:',
    'Y': ':regional_indicator_y:',
    'Z': ':regional_indicator_z:',
    '0': ':zero:',
    '1': ':one:',
    '2': ':two:',
    '3': ':three:',
    '4': ':four:',
    '5': ':five:',
    '6': ':six:',
    '7': ':seven:',
    '8': ':eight:',
    '9': ':nine:',
    '!': ':exclamation:',
    '?': ':question:',
    '#': ':hash:',
    '$': ':dollar:',
    '&': ':arrow_forward:',
    '\'': ':arrow_heading_down:',
    '+': ':heavy_plus_sign:',
    '-': ':heavy_minus_sign:',
    '=': ':aquarius:',
    '*': ':asterisk:',
    '.': ':record_button:',
    '^': ':arrow_forward:',
    '>': ':arrow_right:',
    '<': ':arrow_left:',
    '¥': ':yen:',
    '€': ':euro:',
    '£': ':pound:',
    '_': ':heavy_minus_sign:',
    '‽': ':interrobang:',
    ',': ':arrow_up_small:',
    '’': ':arrow_heading_down:',
    '‘': ':arrow_heading_down:',
    ' ': emojis.blank
})

verbs = {
    -3: "whispers",
    -2: "squeaks",
    -1: "murmurs",
    0: "says",
    1: "shouts",
    2: "roars",
    3: "booms"
}


def resize_text(text, diff):
    """Resizes text to show the relative difference between sizes
    """
    if diff == -3:
        return re.sub(r"[^\s\n]", ".", text)
    elif diff == -2:
        return text.lower().translate(smol_letters)
    elif diff == -1:
        return text.translate(smol_letters)
    elif diff == 0:
        return text
    elif diff == 1:
        return f"**{text}**"
    elif diff == 2:
        return f"**{text.translate(small_caps)}**"
    elif diff == 3:
        return text.translate(giant_letters)


def ratio_to_diff(ratio):
    """Adjust a string to be quiet or loud, and assign it a verb.
    Ratios:
    * ratio < 1/1000: "whispers", convert all letters to periods.
    * 1/1000 < ratio < 1/200: "squeaks", convert letters to lowercase superscript.
    * 1/200 < ratio < 1/12: "murmurs", convert letters to superscript.
    * 1/12 < ratio < 10: "says", do nothing.
    * 10 < ratio < 100: "shouts", convert message to bold.
    * 100 < ratio < 1000: "roars", convert message to small caps bold.
    * 1000 < ratio: "booms", convert message to regional indicators.
    """
    if ratio <= Decimal("1/1000"):
        diff = -3
    elif ratio <= Decimal("1/200"):
        diff = -2
    elif ratio <= Decimal("1/12"):
        diff = -1
    elif ratio <= Decimal(10):
        diff = 0
    elif ratio <= Decimal(100):
        diff = 1
    elif ratio <= Decimal(1000):
        diff = 2
    else:
        diff = 3
    return diff


class SayCog(commands.Cog):
    """Talk to me, boss."""

    def __init__(self, bot):
        self.bot = bot

    @release_on("3.6")
    @commands.command(
        aliases = ["talk"],
        category = "fun",
        multiline = True
    )
    async def say(self, ctx, *, message: str):
        """Talk to the world!"""
        # PERMISSION: requires manage_messages
        await ctx.message.delete(delay=0)

        try:
            user = userdb.load(ctx.guild.id, ctx.author.id)
            height = user.height
            nick = user.nickname
        except UserNotFoundException:
            height = userdb.defaultheight
            nick = ctx.author.display_name

        ratio = height / userdb.defaultheight

        diff = ratio_to_diff(ratio)
        m = resize_text(message, diff)
        verb = verbs[diff]
        await ctx.send(f"{nick} {verb}: \n> {m}")

    @release_on("3.6")
    @commands.command(
        aliases = ["talkto"],
        category = "fun",
        multiline = True
    )
    async def sayto(self, ctx, memberOrHeight: typing.Union[discord.Member, SV], *, message: str):
        """Talk to someone!"""
        # PERMISSION: requires manage_messages
        await ctx.message.delete(delay=0)

        if isinstance(memberOrHeight, SV):
            otherheight = memberOrHeight
            othernick = memberOrHeight.display_name
        else:
            other = userdb.load(ctx.guild.id, memberOrHeight.id)
            otherheight = other.height
            othernick = other.nickname
        try:
            user = userdb.load(ctx.guild.id, ctx.author.id)
            height = user.height
            nick = user.nickname
        except UserNotFoundException:
            height = userdb.defaultheight
            nick = ctx.author.display_name

        ratio = height / otherheight

        diff = ratio_to_diff(ratio)
        m = resize_text(message, diff)
        verb = verbs[diff]
        await ctx.send(f"{nick} {verb} to {othernick}: \n> {m}")


def setup(bot):
    bot.add_cog(SayCog(bot))
