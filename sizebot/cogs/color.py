# import requests
import re

from discord.ext import commands
from sizebot.discordplus import commandsplus

from sizebot.lib.constants import emojis
from sizebot.lib.errors import ArgumentException


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
        splitregex = r",|\s|,\s"
        hexregex = r"#?([0-9A-Fa-f]{3}){1,2}"
        isdigits = r"\d+"
        isdigitsandpercent = r"\d+%?"
        acceptedtypes = ["hex", "rgb", "hsv", "hsl", "cymk"]

        colortype = ""
        colorvalue = ""
        colorvalues = []
        colorvalueout = ""

        # Deafult to hex.
        if not arg2:
            colortype = "hex"
            colorvalue = arg1
        else:
            colortype = arg1
            colorvalue = arg2

        if colortype not in acceptedtypes:
            outmessage.delete()
            raise ArgumentException

        # Make the color value we're putting into the URL be formatted in a way it likes,
        # and also catch any malformed arguments.
        if colortype == "hex":
            if not re.match(colorvalue, hexregex):
                outmessage.delete()
                raise ArgumentException
            if colorvalue.startswith("#"):
                colorvalueout = colorvalue[1:]
            else:
                colorvalueout = colorvalue
        else:
            colorvalues = colorvalue.split(splitregex)
            colorvalueout = colorvalues.join(",")
        if len(colorvalues) not in [3, 4]:
            outmessage.delete()
            raise ArgumentException
        if colortype != "hex" and len(colorvalues) != 3:
            outmessage.delete()
            raise ArgumentException
        if colortype == "rgb":
            for value in colorvalues:
                if not re.match(value, isdigits):
                    outmessage.delete()
                    raise ArgumentException
        elif colortype in ["hsl", "hsv"]:
            if not re.match(colorvalues[0], isdigits):
                outmessage.delete()
                raise ArgumentException
            for value in colorvalues[1:]:
                if not re.match(value, isdigitsandpercent):
                    outmessage.delete()
                    raise ArgumentException
        elif colortype == "cymk":
            for value in colorvalues:
                if not re.match(value, isdigitsandpercent):
                    outmessage.delete()
                    raise ArgumentException

        await outmessage.edit(content = f"You gave me a {colortype} color with the value {colorvalueout}!")

        # r = requests.get(url + "/id?" + colortype + "=" + colorvalueout)
        # colorjson = r.json()


def setup(bot):
    bot.add_cog(ColorCog(bot))
