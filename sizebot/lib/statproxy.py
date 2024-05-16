import logging

from discord.ext import commands

from sizebot.lib.errors import InvalidStat, InvalidStatTag
from sizebot.lib.stats import statmap, taglist

re_full_string = r"\$(\w+=[^;$]+;?)+"
re_component = r"(\w+)=([^;$]+);?"

logger = logging.getLogger("sizebot")


class StatProxy:
    def __init__(self, name: str, tag: bool):
        self.name = name
        self.tag = tag

    def __repr__(self):
        return f"<StatProxy {'#' if self.tag else ''}{self.name}>"

    def __str__(self):
        return self.__repr__()

    @classmethod
    def parse(cls, s: str):
        tag = False
        if s.startswith("#"):
            tag = True
            s = s.removeprefix("#")

        if tag:
            if s not in taglist:
                raise InvalidStatTag(s)
            return StatProxy(s, True)
        else:
            if s not in statmap.keys():
                raise InvalidStat(s)
            return StatProxy(statmap[s], False)

    @classmethod
    async def convert(cls, ctx: commands.Context, argument):
        return cls.parse(argument)
