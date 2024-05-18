from typing import Literal, get_args

from sizebot.lib import errors

Gender = Literal["m", "f"]
GenderOrNone = Gender | None
GENDERS = get_args(Gender)

genders = {
    "m": ("male", "man", "boy"),
    "f": ("female", "woman", "girl"),
    None: ("none", "x", "nb")
}
gendermap = {alias: g for g, aliases in genders.items() for alias in aliases}


def parse_gender(s: str) -> Gender:
    try:
        gender = gendermap[s.lower()]
    except KeyError:
        raise errors.ArgumentException
    return gender
