from typing import Literal, get_args

from sizebot.lib import errors

Gender = Literal["m", "f"]
GENDERS = get_args(Gender)

genders: dict[Gender, list[str]] = {
    "m": ["m", "male", "man", "boy"],
    "f": ["f", "female", "woman", "girl"]
}
gendermap: dict[str, Gender] = {alias: key for key, aliases in genders.items() for alias in aliases}


def parse_gender(s: str) -> Gender:
    gender = gendermap.get(s.lower(), None)
    if gender is None or gender not in GENDERS:
        raise errors.ArgumentException
    return gender
