from sizebot.lib.digidecimal import BaseDecimal, RawDecimal, round_fraction, fix_zeroes


def test_makeSureDecimalStillWorks():
    result = BaseDecimal("1.2") + BaseDecimal("2.3")
    assert result == BaseDecimal("3.5")


def test_roundDecimal_impliedAccuracy():
    result = round(BaseDecimal("2.41"))
    assert result == BaseDecimal("2")


def test_roundDecimal_specifiedAccuracy():
    result = round(BaseDecimal("2.41"), 1)
    assert result == BaseDecimal("2.4")


def test_roundDecimalFraction():
    result = round_fraction(BaseDecimal("2.127"), 8)
    assert result == BaseDecimal("2.125")


def test_toQuarters():
    result = format(BaseDecimal("2.25"), "%4")
    assert result == "2¼"


def test_toQuarters_125():
    result = format(BaseDecimal("2.126"), "%4")
    assert result == "2¼"


def test_toQuarters_noFraction():
    result = format(BaseDecimal("2.01"), "%4")
    assert result == "2"


def test_trimZeros():
    result = fix_zeroes(RawDecimal("100.00"))
    result = str(result)
    assert result == "100"


def test_trimZeros_E():
    result = fix_zeroes(RawDecimal("1E2"))
    result = str(result)
    assert result == "100"
