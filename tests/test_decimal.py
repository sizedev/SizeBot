import pytest

from sizebot.lib.digidecimal import BaseDecimal, RawDecimal, round_fraction, fix_zeroes


def test_make_sure_decimal_still_works() -> None:
    result = BaseDecimal("1.2") + BaseDecimal("2.3")
    assert result == BaseDecimal("3.5")


def test_round_decimal_implied_accuracy() -> None:
    result = round(BaseDecimal("2.41"))
    assert result == BaseDecimal("2")


def test_round_decimal_specified_accuracy() -> None:
    result = round(BaseDecimal("2.41"), 1)
    assert result == BaseDecimal("2.4")


def test_round_decimal_fraction() -> None:
    result = round_fraction(BaseDecimal("2.127"), 8)
    assert result == BaseDecimal("2.125")

@pytest.mark.parametrize(
    ("value", "spec", "expected"),
    [
        (BaseDecimal("2.25"), "%4", "2¼"),
        (BaseDecimal("2.126"), "%4", "2¼"),
        (BaseDecimal("2.01"), "%4", "2"),
    ]
)
def test_to_quarters(value: BaseDecimal, spec: str, expected: str) -> None:
    result = format(value, spec)
    assert result == expected

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (RawDecimal("100.00"), "100"),
        (BaseDecimal("1E2"), "100")
    ]
)
def test_trim_zeros(value: RawDecimal, expected: str) -> None:
    result = str(fix_zeroes(RawDecimal("100.00")))
    assert result == "100"
