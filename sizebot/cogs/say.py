import logging
import typing

import discord
from discord.ext import commands

from sizebot.lib import userdb
from sizebot.lib.constants import emojis
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.units import SV
from sizebot.lib.errors import UserNotFoundException


logger = logging.getLogger("sizebot")

smol_letters = {
  ' ': ' ',
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
}

small_caps = {
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
}

giant_letters = {'a': ':regional_indicator_a:',
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
            'ａ': ':regional_indicator_a:',
            'ｂ': ':regional_indicator_b:',
            'ｃ': ':regional_indicator_c:',
            'ｄ': ':regional_indicator_d:',
            'ｅ': ':regional_indicator_e:',
            'ｆ': ':regional_indicator_f:',
            'ｇ': ':regional_indicator_g:',
            'ｈ': ':regional_indicator_h:',
            'ｉ': ':regional_indicator_i:',
            'ｊ': ':regional_indicator_j:',
            'ｋ': ':regional_indicator_k:',
            'ｌ': ':regional_indicator_l:',
            'ｍ': ':regional_indicator_m:',
            'ｎ': ':regional_indicator_n:',
            'ｏ': ':regional_indicator_o:',
            'ｐ': ':regional_indicator_p:',
            'ｑ': ':regional_indicator_q:',
            'ｒ': ':regional_indicator_r:',
            'ｓ': ':regional_indicator_s:',
            'ｔ': ':regional_indicator_t:',
            'ｕ': ':regional_indicator_u:',
            'ｖ': ':regional_indicator_v:',
            'ｗ': ':regional_indicator_w:',
            'ｘ': ':regional_indicator_x:',
            'ｙ': ':regional_indicator_y:',
            'ｚ': ':regional_indicator_z:',
            'Ａ': ':regional_indicator_a:',
            'Ｂ': ':regional_indicator_b:',
            'Ｃ': ':regional_indicator_c:',
            'Ｄ': ':regional_indicator_d:',
            'Ｅ': ':regional_indicator_e:',
            'Ｆ': ':regional_indicator_f:',
            'Ｇ': ':regional_indicator_g:',
            'Ｈ': ':regional_indicator_h:',
            'Ｉ': ':regional_indicator_i:',
            'Ｊ': ':regional_indicator_j:',
            'Ｋ': ':regional_indicator_k:',
            'Ｌ': ':regional_indicator_l:',
            'Ｍ': ':regional_indicator_m:',
            'Ｎ': ':regional_indicator_n:',
            'Ｏ': ':regional_indicator_o:',
            'Ｐ': ':regional_indicator_p:',
            'Ｑ': ':regional_indicator_q:',
            'Ｒ': ':regional_indicator_r:',
            'Ｓ': ':regional_indicator_s:',
            'Ｔ': ':regional_indicator_t:',
            'Ｕ': ':regional_indicator_u:',
            'Ｖ': ':regional_indicator_v:',
            'Ｗ': ':regional_indicator_w:',
            'Ｘ': ':regional_indicator_x:',
            'Ｙ': ':regional_indicator_y:',
            'Ｚ': ':regional_indicator_z:',
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
            '０': ':zero:',
            '１': ':one:',
            '２': ':two:',
            '３': ':three:',
            '４': ':four:',
            '５': ':five:',
            '６': ':six:',
            '７': ':seven:',
            '８': ':eight:',
            '９': ':nine:',
            ' ': ' ',
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
            '！': ':exclamation:',
            '？': ':question:',
            '＃': ':hash:',
            '＄': ':dollar:',
            '＆': ':arrow_forward:',
            '’': ':arrow_heading_down:',
            '‘': ':arrow_heading_down:',
            '＋': ':heavy_plus_sign:',
            '－': ':heavy_minus_sign:',
            '＝': ':aquarius:',
            '＊': ':asterisk:',
            '．': ':record_button:',
            '＾': ':arrow_forward:',
            '＞': ':arrow_right:',
            '＜': ':arrow_left:',
            '￥': ':yen:',
            '＿': ':heavy_minus_sign:',
            ' ': emojis.blank
}

def adjust_volume(speech, ratio):
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
    newspeech = ""
    if ratio <= Decimal("1/1000"):
        for c in speech:
            if c not in [" ", "\n"]:
                newspeech += "."
            else:
                newspeech += c
        return newspeech, "whispers"
    elif ratio <= Decimal("1/200"):
        for c in speech.lower():
            if c in smol_letters:
                newspeech += smol_letters[c]
            else:
                newspeech += c
        return newspeech, "squeaks"
    elif ratio <= Decimal("1/12"):
        for c in speech:
            if c in smol_letters:
                newspeech += smol_letters[c]
            else:
                newspeech += c
        return newspeech, "murmurs"
    elif ratio <= Decimal(10):
        return speech, "says"
    elif ratio <= Decimal(100):
        return f"**{speech}**", "shouts"
    elif ratio <= Decimal(1000):
        for c in speech:
            if c in small_caps:
                newspeech += small_caps[c]
            else:
                newspeech += c
        return f"**{newspeech}**", "roars"
    else:
        for c in speech:
            if c in giant_letters:
                newspeech += giant_letters[c]
            else:
                newspeech += c
        return f"{newspeech}", "booms"


class SayCog(commands.Cog):
    """Talk to me, boss."""

    def __init__(self, bot):
        self.bot = bot

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

        m, verb = adjust_volume(message, ratio)
        await ctx.send(nick + f" {verb}: \n> " + m)

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
        except:
            height = userdb.defaultheight
            nick = ctx.author.display_name

        ratio = height / otherheight

        m, verb = adjust_volume(message, ratio)
        await ctx.send(f"{nick} {verb} to {othernick}: \n> " + m)


def setup(bot):
    bot.add_cog(SayCog(bot))
