from decimal import Decimal

from sizebot import digiSV
from sizebot.digiSV import SV, WV, TV


def test_toMult():
    result = digiSV.toMult("times 2")
    assert result == 2


def test_TV_parse():
    result = TV.parse("3 seconds")
    assert result == 3


# returns (add amount per second, mult amount per second, size stop, time stop)
def test_toRate_words_add_sizestop():
    result = digiSV.toRate("add 6m per 3 seconds until 12m")
    assert result == (2, 1, 12, None)


def test_toRate_words_add_timestop():
    result = digiSV.toRate("add 6m per 3 seconds for 10 seconds")
    assert result == (2, 1, None, 10)


def test_toRate_words_add_nostop():
    result = digiSV.toRate("add 6m per 3 seconds")
    assert result == (2, 1, None, None)


def test_toRate_words_sub_sizestop():
    result = digiSV.toRate("subtract 6m per 3 seconds until 12m")
    assert result == (-2, 1, 12, None)


def test_toRate_words_sub_timestop():
    result = digiSV.toRate("subtract 6m per 3 seconds for 10 seconds")
    assert result == (-2, 1, None, 10)


def test_toRate_words_sub_nostop():
    result = digiSV.toRate("subtract 6m per 3 seconds")
    assert result == (-2, 1, None, None)


def test_toRate_words_mult_sizestop():
    result = digiSV.toRate("multiply 8 per 3 seconds until 12m")
    assert result == (0, 2, 12, None)


def test_toRate_words_mult_timestop():
    result = digiSV.toRate("times 8 per 3 seconds for 10 seconds")
    assert result == (0, 2, None, 10)


def test_toRate_words_mult_nostop():
    result = digiSV.toRate("times 8 per 3 seconds")
    assert result == (0, 2, None, None)


def test_toRate_words_div_sizestop():
    result = digiSV.toRate("divide 8 per 3 seconds until 12m")
    assert result == (0, Decimal(0.5), 12, None)


def test_toRate_words_div_timestop():
    result = digiSV.toRate("divide 8 per 3 seconds for 10 seconds")
    assert result == (0, Decimal(0.5), None, 10)


def test_toRate_words_div_nostop():
    result = digiSV.toRate("divide 8 per 3 seconds")
    assert result == (0, Decimal(0.5), None, None)


# symbols
def test_toRate_symbols_add_sizestop():
    result = digiSV.toRate("6m/3s until 12m")
    assert result == (2, 1, 12, None)


def test_toRate_symbols_add_timestop():
    result = digiSV.toRate("add 6m/3s for 10 seconds")
    assert result == (2, 1, None, 10)


def test_toRate_symbols_add_nostop():
    result = digiSV.toRate("6m/3s")
    assert result == (2, 1, None, None)


def test_toRate_symbols_sub_sizestop():
    result = digiSV.toRate("-6m/3s until 12m")
    assert result == (-2, 1, 12, None)


def test_toRate_symbols_sub_timestop():
    result = digiSV.toRate("-6m/3s->10s")
    assert result == (-2, 1, None, 10)


def test_toRate_symbols_sub_nostop():
    result = digiSV.toRate("-6m/3s")
    assert result == (-2, 1, None, None)


def test_toRate_symbols_mult_sizestop():
    result = digiSV.toRate("x8/3s until 12m")
    assert result == (0, 2, 12, None)


def test_toRate_symbols_mult_timestop():
    result = digiSV.toRate("*8/3s for 10s")
    assert result == (0, 2, None, 10)


def test_toRate_symbols_mult_nostop():
    result = digiSV.toRate("x8/3s")
    assert result == (0, 2, None, None)


def test_toRate_symbols_div_sizestop():
    result = digiSV.toRate("/8/3s until 12m")
    assert result == (0, Decimal("0.5"), 12, None)


def test_toRate_symbols_div_timestop():
    result = digiSV.toRate("/8/3s for 10s")
    assert result == (0, Decimal("0.5"), None, 10)


def test_toRate_symbols_div_nostop():
    result = digiSV.toRate("/8/3s")
    assert result == (0, Decimal("0.5"), None, None)


def test_toRate_2x():
    result = digiSV.toRate("8x/3s")
    assert result == (0, 2, None, None)


def test_toRate_omitOne():
    result = digiSV.toRate("2 meters per second")
    assert result == (2, 1, None, None)


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
