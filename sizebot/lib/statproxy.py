from __future__ import annotations

from sizebot.lib.errors import InvalidStat, InvalidStatTag
from sizebot.lib.stats import get_mapped_stat, taglist
from sizebot.lib.types import BotContext

re_full_string = r"\$(\w+=[^;$]+;?)+"
re_component = r"(\w+)=([^;$]+);?"


class StatProxy:
    def __init__(self, name: str, tag: bool):
        self.name = name
        self.tag = tag

    def __repr__(self) -> str:
        return f"<StatProxy {'#' if self.tag else ''}{self.name}>"

    def __str__(self) -> str:
        return self.__repr__()

    @classmethod
    def parse(cls, s: str) -> StatProxy:
        tag: bool = False
        if s.startswith("#"):
            tag = True
            s = s.removeprefix("#")

        if tag:
            if s not in taglist:
                raise InvalidStatTag(s)
            return StatProxy(s, True)
        else:
            mapped = get_mapped_stat(s)
            if mapped is None:
                raise InvalidStat(s)
            return StatProxy(mapped, False)

    @classmethod
    async def convert(cls, ctx: BotContext, argument: str) -> StatProxy:
        return cls.parse(argument)
