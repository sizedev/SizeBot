from typing import Literal, get_args

from sizebot.lib import errors
from sizebot.lib.utils import AliasMapper

Gender = Literal["m", "f"]
GENDERS = get_args(Gender)

gendermap = AliasMapper[Gender]({
    "m": ["male", "man", "boy"],
    "f": ["female", "woman", "girl"]
})


def parse_gender(s: str) -> Gender:
    if s not in gendermap:
        raise errors.ArgumentException
    gender = gendermap[s]
    return gender
