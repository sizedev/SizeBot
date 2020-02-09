# import requests
import re

from discord.ext import commands
from sizebot.discordplus import commandsplus

from sizebot.lib.constants import emojis


re_hex = re.compile(r"#?((?:[0-9A-Fa-f]{3}){1,2})")
re_digits = re.compile(r"\d+")
re_percent = re.compile(r"\d+%?")
re_dividers = re.compile(r"[\s,]+")


class ColorCog(commands.Cog):
    """Commands for non-size stuff."""

    def __init__(self, bot):
        self.bot = bot

    @commandsplus.command(
        aliases = ["colour"],
        usage = "[hex/rgb/hsv/hsl/cymk] <colorcode>"
    )
    async def color(self, ctx, arg1: str, *, arg2: str = None):
        outmessage = await ctx.send(emojis.loading)

        # url = "http://thecolorapi.com"

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
                await outmessage.edit(content = f"{value} is not a valid color part for a {colortype}-type color.")
                return
            for value in colorvalues[1:]:
                if not re_percent.match(value):
                    await outmessage.edit(content = f"{value} is not a valid color part for a {colortype}-type color.")
                    return
            colorvalueout = ",".join(colorvalues)
        elif colortype == "cymk":
            # CYMK
            if len(colorvalues) not in [3, 4]:
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

        await outmessage.edit(content = f"You gave me a {colortype} color with the value {colorvalueout}!")

        # r = requests.get(url + "/id?" + colortype + "=" + colorvalueout)
        # colorjson = r.json()


def setup(bot):
    bot.add_cog(ColorCog(bot))
