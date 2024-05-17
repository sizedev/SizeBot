from sizebot.lib import units
from sizebot.lib.shoesize import to_shoe_size, from_shoe_size
from sizebot.lib.units import SV, WV, TV, Mult

units.init()


def test_Mult_parse():
    result = Mult.parse("times 2")
    assert result == 2


def test_TV_parse():
    result = TV.parse("3 seconds")
    assert result == 3


def test_negative_SV_parse():
    result = SV.parse("-12m")
    assert result == SV("-12")


def test_negative_SV_format():
    result = f"{SV('-12'):m}"
    assert result == "-12m"


def test_negative_WV_parse():
    result = WV.parse("-12kg")
    assert result == WV("-12000")


def test_negative_WV_format():
    result = f"{WV('-12000'):m}"
    assert result == "-12kg"


def test_feetinch_noinchunit():
    result = SV.parse("5ft8")
    assert result == SV("1.7272")


def test_reverse_shoesize_calc():
    insize = SV.parse("10in")
    shoesize = to_shoe_size(insize, "m")
    outsize = from_shoe_size(shoesize)
    assert insize == outsize
