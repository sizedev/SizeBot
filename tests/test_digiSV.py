from decimal import Decimal

from sizebot.digiSV import SV, WV, TV, Mult, Rate


def test_parseMult():
    result = Mult.parse("times 2")
    assert result == 2


def test_TV_parse():
    result = TV.parse("3 seconds")
    assert result == 3


# returns (add amount per second, mult amount per second, size stop, time stop)
def test_parseRate_words_add_sizestop():
    result = Rate.parse("add 6m per 3 seconds until 12m")
    assert result == (2, 1, 12, None)


def test_parseRate_words_add_timestop():
    result = Rate.parse("add 6m per 3 seconds for 10 seconds")
    assert result == (2, 1, None, 10)


def test_parseRate_words_add_nostop():
    result = Rate.parse("add 6m per 3 seconds")
    assert result == (2, 1, None, None)


def test_parseRate_words_sub_sizestop():
    result = Rate.parse("subtract 6m per 3 seconds until 12m")
    assert result == (-2, 1, 12, None)


def test_parseRate_words_sub_timestop():
    result = Rate.parse("subtract 6m per 3 seconds for 10 seconds")
    assert result == (-2, 1, None, 10)


def test_parseRate_words_sub_nostop():
    result = Rate.parse("subtract 6m per 3 seconds")
    assert result == (-2, 1, None, None)


def test_parseRate_words_mult_sizestop():
    result = Rate.parse("multiply 8 per 3 seconds until 12m")
    assert result == (0, 2, 12, None)


def test_parseRate_words_mult_timestop():
    result = Rate.parse("times 8 per 3 seconds for 10 seconds")
    assert result == (0, 2, None, 10)


def test_parseRate_words_mult_nostop():
    result = Rate.parse("times 8 per 3 seconds")
    assert result == (0, 2, None, None)


def test_parseRate_words_div_sizestop():
    result = Rate.parse("divide 8 per 3 seconds until 12m")
    assert result == (0, Decimal(0.5), 12, None)


def test_parseRate_words_div_timestop():
    result = Rate.parse("divide 8 per 3 seconds for 10 seconds")
    assert result == (0, Decimal(0.5), None, 10)


def test_parseRate_words_div_nostop():
    result = Rate.parse("divide 8 per 3 seconds")
    assert result == (0, Decimal(0.5), None, None)


# symbols
def test_parseRate_symbols_add_sizestop():
    result = Rate.parse("6m/3s until 12m")
    assert result == (2, 1, 12, None)


def test_parseRate_symbols_add_timestop():
    result = Rate.parse("add 6m/3s for 10 seconds")
    assert result == (2, 1, None, 10)


def test_parseRate_symbols_add_nostop():
    result = Rate.parse("6m/3s")
    assert result == (2, 1, None, None)


def test_parseRate_symbols_sub_sizestop():
    result = Rate.parse("-6m/3s until 12m")
    assert result == (-2, 1, 12, None)


def test_parseRate_symbols_sub_timestop():
    result = Rate.parse("-6m/3s->10s")
    assert result == (-2, 1, None, 10)


def test_parseRate_symbols_sub_nostop():
    result = Rate.parse("-6m/3s")
    assert result == (-2, 1, None, None)


def test_parseRate_symbols_mult_sizestop():
    result = Rate.parse("x8/3s until 12m")
    assert result == (0, 2, 12, None)


def test_parseRate_symbols_mult_timestop():
    result = Rate.parse("*8/3s for 10s")
    assert result == (0, 2, None, 10)


def test_parseRate_symbols_mult_nostop():
    result = Rate.parse("x8/3s")
    assert result == (0, 2, None, None)


def test_parseRate_symbols_div_sizestop():
    result = Rate.parse("/8/3s until 12m")
    assert result == (0, Decimal("0.5"), 12, None)


def test_parseRate_symbols_div_timestop():
    result = Rate.parse("/8/3s for 10s")
    assert result == (0, Decimal("0.5"), None, 10)


def test_parseRate_symbols_div_nostop():
    result = Rate.parse("/8/3s")
    assert result == (0, Decimal("0.5"), None, None)


def test_parseRate_2x():
    result = Rate.parse("8x/3s")
    assert result == (0, 2, None, None)


def test_parseRate_omitOne():
    result = Rate.parse("2 meters per second")
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
