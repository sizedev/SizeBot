import re

from sizebot.lib.diff import Rate as ParseableRate
from sizebot.lib.errors import InvalidSizeValue, InvalidStat
from sizebot.lib.proportions import fromShoeSize
from sizebot.lib.userdb import User
from sizebot.lib.units import SV, WV
from sizebot.lib.utils import AliasMap, parse_scale, truthy

re_full_string = r"\$(\w+=[^;$]+;)?(\w+=[^;$]+)"
re_component = r"(\w+)=([^;$]+);?"


class FakePlayer(User):
    """Generates a fake User based on a dumb string with complex syntax no one will use but me."""
    KEYMAP = AliasMap({
        "nickname": ("nick", "name"),
        "height": (),
        "baseheight": (),
        "baseweight": (),
        "footlength": ("foot"),
        "shoesize": ("shoe"),
        "hairlength": ("hair"),
        "taillength": ("tail"),
        "earheight": ("ear"),
        "pawtoggle": ("paw"),
        "furtoggle": ("fur"),
        "liftstrength": ("lift", "carry"),
        "walkperhour": ("walk"),
        "runperhour": ("run"),
        "swimperhour": ("swim"),
        "gender": (),
        "scale": ()
    })

    UNITMAP = {
        "nickname": str,
        "height": SV,
        "baseheight": SV,
        "baseweight": WV,
        "footlength": SV,
        "shoesize": str,
        "hairlength": SV,
        "taillength": SV,
        "earheight": SV,
        "pawtoggle": bool,
        "furtoggle": bool,
        "liftstrength": WV,
        "walkperhour": ParseableRate,
        "runperhour": ParseableRate,
        "swimperhour": ParseableRate,
        "gender": str,
        "scale": str
    }

    @classmethod
    def parse(cls, s: str):
        match = re.match(re_full_string, s)
        if match is None:
            raise InvalidSizeValue(s, "FakePlayer")

        player = FakePlayer()

        for group in match.groups():
            componentmatch = re.match(re_component, group)
            key = componentmatch.group(1)
            val = componentmatch.group(2)
            if key not in cls.KEYMAP:
                raise InvalidStat(key)

            collapsed_key = cls.KEYMAP[key]
            unit = cls.UNITMAP[collapsed_key]

            if collapsed_key == "scale":
                player.scale = parse_scale(val)
            elif collapsed_key == "shoesize":
                player.footlength = fromShoeSize(val)
            elif unit == bool:
                setattr(player, collapsed_key, truthy(val))
            elif unit == str:
                setattr(player, collapsed_key, val)
            elif unit in (SV, WV, ParseableRate):
                val = unit.parse(val)
                setattr(player, collapsed_key, val)

        if player.nickname is None:
            player.nickname = f"a {player.height:,.3mu} tall person"

        return player

    @classmethod
    async def convert(cls, ctx, argument):
        return cls.parse(argument)
