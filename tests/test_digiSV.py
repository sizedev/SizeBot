from sizebot import digiSV


def test_toMult():
    result = digiSV.toMult("times 2")
    assert result == 2


def test_toTV():
    result = digiSV.toTV("3 seconds")
    assert result == 3


def test_toRate():
    result = digiSV.toRate("add 6m per 3 seconds until 12m")
    assert result == (2, 1, 12, None)
