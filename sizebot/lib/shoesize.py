from typing import Literal

import re

from sizebot.lib.digidecimal import Decimal
from sizebot.lib.units import SV


def to_shoe_size(footlength: SV, gender: Literal["m", "f"]):
    women = gender == "f"
    # Inch in meters
    inch = Decimal("0.0254")
    footlengthinches = footlength / inch
    shoesizeNum = (3 * (footlengthinches + Decimal("2/3"))) - 24
    prefix = ""
    if shoesizeNum < 1:
        prefix = "Children's "
        women = False
        shoesizeNum += 12 + Decimal("1/3")
    if shoesizeNum < 0:
        return "No shoes exist this small!"
    if women:
        shoesize = format(Decimal(shoesizeNum + 1), ",.2%2")
    else:
        shoesize = format(Decimal(shoesizeNum), ",.2%2")
    if women:
        return f"Size US Women's {prefix}{shoesize}"
    return f"Size US {prefix}{shoesize}"


def from_shoe_size(shoesize: str) -> SV:
    shoesizenum = unmodifiedshoesizenum = Decimal(re.search(r"(\d*,)*\d+(\.\d*)?", shoesize)[0])
    if "w" in shoesize.lower():
        shoesizenum = unmodifiedshoesizenum - 1
    if "c" in shoesize.lower():  # Intentional override, children's sizes have no women/men distinction.
        shoesizenum = unmodifiedshoesizenum - (12 + Decimal("1/3"))
    footlengthinches = ((shoesizenum + 24) / 3) - Decimal("2/3")
    return SV.parse(f"{footlengthinches}in")
