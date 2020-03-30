# import discord

# from sizebot import __version__
from sizebot.lib.units import SV, WV


class ObjectComparison:
    def __init__(self, userdata, obj):
        self.multiplier = self.userdata.viewscale

        self.perceivedlength = obj.length and SV(obj.length * self.multiplier)
        self.perceivedheight = obj.height and SV(obj.height * self.multiplier)
        self.perceivedwidth = obj.width and SV(obj.width * self.multiplier)
        self.perceiveddepth = obj.depth and SV(obj.depth * self.multiplier)
        self.perceivedweight = obj.weight and WV(obj.weight * (self.multiplier ** 3))

    def __str__(self):
        returnstr = f"{self.userdata.nickname} is {self.userdata.height:,.3mu} tall.\n"
        returnstr += f"To {self.userdata.nickname}..."
        return returnstr
