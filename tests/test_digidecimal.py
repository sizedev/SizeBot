import sizebot.digidecimal as digidecimal
from sizebot.digidecimal import Decimal


def test_makeSureDecimalStillWorks():
    result = Decimal("1.2") + Decimal("2.3")
    assert result == Decimal("3.5")


def test_roundDecimal_impliedAccuracy():
    result = digidecimal.roundDecimal(Decimal("2.41"))
    assert result == Decimal("2")


def test_roundDecimal_specifiedAccuracy():
    result = digidecimal.roundDecimal(Decimal("2.41"), 1)
    assert result == Decimal("2.4")


def test_roundDecimalFraction():
    result = digidecimal.roundDecimalFraction(Decimal("2.127"), 8)
    assert result == Decimal("2.125")


def test_toEighths():
    result = digidecimal.toEighths(Decimal("2.125"))
    assert result == "2⅛"


def test_toEights_noFraction():
    result = digidecimal.toEights(Decimal("2.01"))
    assert result == "2"


def test_trimZeros():
    result = digidecimal.trimZeros(Decimal("100.00"))
    result = str(result)
    assert result == "100"


def test_trimZeros_E():
    result = digidecimal.trimZeros(Decimal("1E2"))
    result = str(result)
    assert result == "100"
