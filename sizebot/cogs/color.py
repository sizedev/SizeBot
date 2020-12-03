from json.decoder import JSONDecodeError
import re
import requests

from discord import Embed
from discord.ext import commands

from sizebot import __version__
from sizebot.lib.constants import emojis


re_hex = re.compile(r"#?((?:[0-9A-Fa-f]{3}){1,2})")
re_digits = re.compile(r"\d+")
re_percent = re.compile(r"\d+%?")
re_dividers = re.compile(r"[\s,]+")
coloricon = "https://cdn.discordapp.com/attachments/650460192009617433/676205298674958366/spinning-beachball-of-death-mac.png"


class ColorCog(commands.Cog):
    """Commands for non-size stuff."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases = ["colour"],
        usage = "[hex/rgb/hsv/hsl/cymk] <colorcode>",
        category = "fun"
    )
    async def color(self, ctx, arg1: str, *, arg2: str = None):
        """Get info about a color."""
        outmessage = await ctx.send(emojis.loading)

        url = "http://thecolorapi.com"
        schemeurl = "https://www.thecolorapi.com/scheme?hex={0}&format=html"

        # Default to hex.
        if not arg2:
            colortype = "hex"
            colorvalue = arg1
        else:
            colortype = arg1.lower()
            colorvalue = arg2

        colorvalues = re_dividers.split(colorvalue)

        # Make the color value we're putting into the URL be formatted in a way it likes,
        # and also catch any malformed arguments.
        if colortype == "hex":
            # HEX
            match_hex = re_hex.match(colorvalue)
            if not match_hex:
                await outmessage.edit(content = f"`{colorvalue}` is not an accepted hex color.")
                return
            colorvalueout = match_hex.group(1)
        elif colortype == "rgb":
            # RGB
            if len(colorvalues) != 3:
                await outmessage.edit(content = f"A {colortype} color can only have 3 parts.")
                return
            for value in colorvalues:
                if not re_digits.match(value):
                    await outmessage.edit(content = f"{value} is not a valid color part for a {colortype}-type color.")
                    return
            colorvalueout = ",".join(colorvalues)
        elif colortype in ["hsl", "hsv"]:
            # HSL/HSV
            if len(colorvalues) != 3:
                await outmessage.edit(content = f"A {colortype} color can only have 3 parts.")
                return
            if not re_digits.match(colorvalues[0]):
                await outmessage.edit(content = f"{colorvalue} is not a valid color part for a {colortype}-type color.")
                return
            for value in colorvalues[1:]:
                if not re_percent.match(value):
                    await outmessage.edit(content = f"{value} is not a valid color part for a {colortype}-type color.")
                    return
            colorvalueout = ",".join(colorvalues)
        elif colortype in ["cmyk", "cymk"]:
            # CMYK
            colortype = "cmyk"
            if len(colorvalues) != 4:
                await outmessage.edit(content = f"A {colortype} color can only have between 3 and 4 parts.")
                return
            for value in colorvalues:
                if not re_percent.match(value):
                    await outmessage.edit(content = f"{value} is not a valid color part for a {colortype}-type color.")
                    return
            colorvalueout = ",".join(colorvalues)
        else:
            # Invalid color type
            await outmessage.edit(content = f"`{colortype}` is not an accepted color type.\nAccepted types are hex, rgb, hsv, hsl, or cymk.")
            return

        r = requests.get(url + "/id?" + colortype + "=" + colorvalueout)
        try:
            colorjson = r.json()
        except JSONDecodeError:
            await outmessage.edit(emojis.warning + "The Color API is not working as expected. Please try again later.")
            return

        if r.status_code != 200:
            await outmessage.edit(emojis.warning + "The Color API is not working as expected. Please try again later.")
            return
            
        hexstring = colorjson["hex"]["clean"]
        hexvalue = int(hexstring, 16)
        colorscheme = schemeurl.format(hexstring)
        colorname = colorjson["name"]["value"]
        printhex = colorjson["hex"]["value"]
        colorrgb = colorjson["rgb"]["value"]
        colorhsl = colorjson["hsl"]["value"]
        colorhsv = colorjson["hsv"]["value"]
        colorcmyk = colorjson["cmyk"]["value"]

        embed = Embed(title=f"{colorname} [{printhex}]",
                            description="",
                            color=hexvalue,
                            url=colorscheme)
        embed.set_author(name=f"SizeBot {__version__} [{ctx.prefix}color]", icon_url=coloricon)
        embed.add_field(name="Hex Value", value = printhex, inline = True)
        embed.add_field(name="RGB Value", value = colorrgb, inline = True)
        embed.add_field(name="HSL Value", value = colorhsl, inline = True)
        embed.add_field(name="HSV Value", value = colorhsv, inline = True)
        embed.add_field(name="CMYK Value", value = colorcmyk, inline = True)
        embed.set_footer(text = f"Requested by {ctx.author.display_name}")

        embed.set_image(url = f"http://www.singlecolorimage.com/get/{hexstring}/400x200.png")

        await outmessage.edit(content = "", embed = embed)


def setup(bot):
    bot.add_cog(ColorCog(bot))
