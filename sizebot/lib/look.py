# import discord

# from sizebot import __version__
from sizebot.lib.constants import emojis
from sizebot.lib.units import SV, WV


class ObjectComparison:
    def __init__(self, userdata, obj):
        self.userdata = userdata
        self.multiplier = self.userdata.viewscale
        self.obj = obj

        self.perceivedlength = self.obj.length and SV(self.obj.length * self.multiplier)
        self.perceivedheight = self.obj.height and SV(self.obj.height * self.multiplier)
        self.perceivedwidth = self.obj.width and SV(self.obj.width * self.multiplier)
        self.perceiveddepth = self.obj.depth and SV(self.obj.depth * self.multiplier)
        self.perceivedweight = self.obj.weight and WV(self.obj.weight * (self.multiplier ** 3))

    def __str__(self):
        returnstr = f"{self.userdata.nickname} is {self.userdata.height:,.3mu} tall.\n"
        returnstr += f"To {self.userdata.nickname}, {self.obj.article} looks...\n"
        if not self.perceivedheight:
            returnstr += f"{emojis.blank}{self.perceivedlength:,.3mu} tall\n"
        if self.perceivedheight:
            returnstr += f"{emojis.blank}{self.perceivedheight:,.3mu} tall\n"
        if self.perceivedwidth:
            returnstr += f"{emojis.blank}{self.perceivedwidth:,.3mu} wide\n"
        if self.perceiveddepth:
            returnstr += f"{emojis.blank}{self.perceiveddepth:,.3mu} deep\n"
        if self.perceivedweight:
            returnstr += "and weighs"
            returnstr += f"{emojis.blank}{self.perceivedweight:,.3mu}"
        return returnstr
