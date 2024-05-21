from __future__ import annotations
from typing import Any, Generic, TypeVar
from collections.abc import Callable

import re

from discord.ext.commands.converter import _convert_to_bool as truthy

from sizebot.lib.diff import Rate
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.errors import InvalidSizeValue, InvalidStat
from sizebot.lib.shoesize import from_shoe_size
from sizebot.lib.types import BotContext
from sizebot.lib.units import SV, WV
from sizebot.lib.utils import parse_scale
from sizebot.lib.stats import HOUR, get_mapped_stat

T = TypeVar("T")


class FakePlayerStat(Generic[T]):
    def __init__(self, name: str, parser: Callable[[str], T], *, saveas: str | None = None):
        self.name = name
        self.parse = parser
        self.saveas = saveas or name


fakestats_list: list[FakePlayerStat] = [
    FakePlayerStat("nickname", str),
    FakePlayerStat("height", SV.parse),
    FakePlayerStat("baseheight", SV.parse),
    FakePlayerStat("baseweight", WV.parse),
    FakePlayerStat("footlength", SV.parse),
    FakePlayerStat("shoesize", from_shoe_size, saveas="footlength"),
    FakePlayerStat("hairlength", SV.parse),
    FakePlayerStat("taillength", SV.parse),
    FakePlayerStat("earheight", SV.parse),
    FakePlayerStat("pawtoggle", truthy),
    FakePlayerStat("furtoggle", truthy),
    FakePlayerStat("liftstrength", WV.parse),
    FakePlayerStat("walkperhour", lambda s: Rate.parse(s).addPerSec * HOUR),
    FakePlayerStat("runperhour", lambda s: Rate.parse(s).addPerSec * HOUR),
    FakePlayerStat("swimperhour", lambda s: Rate.parse(s).addPerSec * HOUR),
    FakePlayerStat("gender", str),
    FakePlayerStat("scale", parse_scale)
]

fakestats = {stat.name: stat for stat in fakestats_list}


def parse_keyvalues(s: str) -> dict[str, Any]:
    # $key=value;key=value;key=value...
    re_full = r"\$((?:\w+=[^;$=]+;?)+)"
    m = re.match(re_full, s)
    if m is None:
        raise InvalidSizeValue(s, "FakePlayer")
    full = m.group(1)
    allkeyvalues = [parse_keyvalue(kv_str) for kv_str in full.split(";")]
    keyvalues = {k: v for k, v in allkeyvalues if v is not None}
    return keyvalues


def parse_keyvalue(kv_str: str) -> tuple[str, Any]:
    # key=value
    re_keyvalue = r"(\w+)=([^;$=]+)"
    m = re.match(re_keyvalue, kv_str)
    if m is None:
        raise InvalidSizeValue(kv_str, "FakePlayer")
    key, val_str = m.groups()
    # Special exception for shoesize where we _actually_ set footlength
    if key != "shoesize":
        key = get_mapped_stat(key)
    if key not in fakestats:
        raise InvalidStat(key)
    stat = fakestats[key]
    savekey = stat.saveas
    val = stat.parse(val_str)
    return savekey, val


class FakePlayer:
    """Generates a fake User based on a dumb string with complex syntax no one will use but me."""

    def __init__(
        self,
        *,
        nickname: str | None = None,
        height: SV | None = None,
        baseheight: SV | None = None,
        baseweight: WV | None = None,
        footlength: SV | None = None,
        hairlength: SV | None = None,
        taillength: SV | None = None,
        earheight: SV | None = None,
        pawtoggle: bool | None = None,
        furtoggle: bool | None = None,
        liftstrength: WV | None = None,
        walkperhour: SV | None = None,
        runperhour: SV | None = None,
        swimperhour: SV | None = None,
        gender: str | None = None,
        scale: Decimal | None = None,
    ):
        self.statvalues: dict[str, Any] = {}
        if nickname is not None:
            self.statvalues["nickname"] = nickname
        else:
            self.statvalues["nickname"] = f"a {height:,.3mu} tall person"
        if height is not None:
            self.statvalues["height"] = height
        if baseheight is not None:
            self.statvalues["baseheight"] = baseheight
        if baseweight is not None:
            self.statvalues["baseweight"] = baseweight
        if footlength is not None:
            self.statvalues["footlength"] = footlength
        if hairlength is not None:
            self.statvalues["hairlength"] = hairlength
        if taillength is not None:
            self.statvalues["taillength"] = taillength
        if earheight is not None:
            self.statvalues["earheight"] = earheight
        if pawtoggle is not None:
            self.statvalues["pawtoggle"] = pawtoggle
        if furtoggle is not None:
            self.statvalues["furtoggle"] = furtoggle
        if liftstrength is not None:
            self.statvalues["liftstrength"] = liftstrength
        if walkperhour is not None:
            self.statvalues["walkperhour"] = walkperhour
        if runperhour is not None:
            self.statvalues["runperhour"] = runperhour
        if swimperhour is not None:
            self.statvalues["swimperhour"] = swimperhour
        if gender is not None:
            self.statvalues["gender"] = gender
        if scale is not None:
            self.statvalues["scale"] = scale

    @classmethod
    def parse(cls, s: str) -> FakePlayer:
        # $key=value;key=value;key=value...
        keyvalues = parse_keyvalues(s)
        player = FakePlayer(**keyvalues)
        return player

    @classmethod
    async def convert(cls, ctx: BotContext, argument: str) -> FakePlayer:
        return cls.parse(argument)
