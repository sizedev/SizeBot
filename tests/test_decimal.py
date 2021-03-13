from sizebot.lib.utils import roundFraction, fixZeroes
from sizebot.lib.digidecimal import Decimal, RawDecimal


def test_makeSureDecimalStillWorks():
    result = Decimal("1.2") + Decimal("2.3")
    assert result == Decimal("3.5")


def test_roundDecimal_impliedAccuracy():
    result = round(Decimal("2.41"))
    assert result == Decimal("2")


def test_roundDecimal_specifiedAccuracy():
    result = round(Decimal("2.41"), 1)
    assert result == Decimal("2.4")


def test_roundDecimalFraction():
    result = roundFraction(Decimal("2.127"), 8)
    assert result == Decimal("2.125")


def test_toQuarters():
    result = format(Decimal("2.25"), "%4")
    assert result == "2¼"


def test_toQuarters_125():
    result = format(Decimal("2.126"), "%4")
    assert result == "2¼"


def test_toQuarters_noFraction():
    result = format(Decimal("2.01"), "%4")
    assert result == "2"


def test_trimZeros():
    result = fixZeroes(RawDecimal("100.00"))
    result = str(result)
    assert result == "100"


def test_trimZeros_E():
    result = fixZeroes(RawDecimal("1E2"))
    result = str(result)
    assert result == "100"
