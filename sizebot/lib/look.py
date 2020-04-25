# import discord

# from sizebot import __version__
from sizebot.lib.constants import emojis
from sizebot.lib.units import SV, WV


class ObjectComparison:
    def __init__(self, userdata, obj):
        self.userdata = userdata
        self.multiplier = self.userdata.viewscale
        self.obj = obj

        self.perceivedheight = self.obj.height and SV(self.obj.height * self.multiplier)
        self.perceivedlength = self.obj.length and SV(self.obj.length * self.multiplier)
        self.perceivedwidth = self.obj.width and SV(self.obj.width * self.multiplier)
        self.perceiveddiameter = self.obj.diameter and SV(self.obj.diameter * self.multiplier)
        self.perceiveddepth = self.obj.depth and SV(self.obj.depth * self.multiplier)
        self.perceivedthickness = self.obj.thickness and SV(self.obj.thickness * self.multiplier)
        self.perceivedweight = self.obj.weight and WV(self.obj.weight * (self.multiplier ** 3))

    def __str__(self):
        returnstr = f"__{self.userdata.nickname} is {self.userdata.height:,.3mu} tall.__\n"
        returnstr += f"To {self.userdata.nickname}, {self.obj.article} {self.obj.name} looks...\n"
        if not self.perceivedheight:
            returnstr += f"{emojis.blank}{self.perceivedlength:,.3mu} tall\n"
        if self.perceivedheight:
            returnstr += f"{emojis.blank}{self.perceivedheight:,.3mu} tall\n"
        if self.perceivedwidth:
            returnstr += f"{emojis.blank}{self.perceivedwidth:,.3mu} wide\n"
        if self.perceiveddepth:
            returnstr += f"{emojis.blank}{self.perceiveddepth:,.3mu} deep\n"
        if self.perceivedweight:
            returnstr += "and weighs...\n"
            returnstr += f"{emojis.blank}{self.perceivedweight:,.3mu}"
        return returnstr

    # TODO: Add a toEmbed() method.


class ObjectStats:
    def __init__(self, obj):
        self.height = self.obj.height and SV(self.obj.height)
        self.length = self.obj.length and SV(self.obj.length)
        self.width = self.obj.width and SV(self.obj.width)
        self.diameter = self.obj.diameter and SV(self.obj.diameter)
        self.depth = self.obj.depth and SV(self.obj.depth)
        self.thickness = self.obj.thickness and SV(self.obj.thickness)
        self.weight = self.obj.weight and WV(self.obj.weight)

    def __str__(self):
        returnstr = f"{self.obj.article.capitalize()} {self.obj.name} is...\n"
        if self.height:
            returnstr += f"{emojis.blank}{self.height:,.3mu} tall\n"
        if self.length:
            returnstr += f"{emojis.blank}{self.length:,.3mu} long\n"
        if self.width:
            returnstr += f"{emojis.blank}{self.width:,.3mu} wide\n"
        if self.diameter:
            returnstr += f"{emojis.blank}{self.diameter:,.3mu} across\n"
        if self.depth:
            returnstr += f"{emojis.blank}{self.depth:,.3mu} deep\n"
        if self.thickness:
            returnstr += f"{emojis.blank}{self.depth:,.3mu} thick\n"
        if self.weight:
            returnstr += "and weighs...\n"
            returnstr += f"{emojis.blank}{self.weight:,.3mu}"

        return returnstr
