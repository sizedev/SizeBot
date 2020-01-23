import math
from sizebot.digidecimal import Decimal

posinf = Decimal("infinity")
neginf = Decimal("-infinity")


def test_pos__str__():
    result = format(posinf)
    assert result == "∞"


def test_neg__str__():
    result = format(neginf)
    assert result == "-∞"


def test_pos__repr__():
    result = repr(posinf)
    assert result == "Decimal('∞')"


def test_neg__repr__():
    result = repr(neginf)
    assert result == "Decimal('-∞')"


def test_pos__bool__():
    result = bool(posinf)
    assert result is True


def test_neg__bool__():
    result = bool(neginf)
    assert result is True


def test_pos__eq__():
    result = posinf == posinf
    assert result is True


def test_neg__eq__():
    result = neginf == neginf
    assert result is True


def test_pos__lt__():
    result = 0 < posinf
    assert result is True


def test_neg__lt__():
    result = 0 < neginf
    assert result is False


def test_pos__add__():
    result = posinf + 1
    assert result == posinf


def test_neg__add__():
    result = neginf + 1
    assert result == neginf


def test_pos__sub__():
    result = posinf - 1
    assert result == posinf


def test_neg__sub__():
    result = neginf - 1
    assert result == neginf


def test_pos__rsub__():
    result = 1 - posinf
    assert result == neginf


def test_neg__rsub__():
    result = 1 - neginf
    assert result == posinf


def test_pos__mul__():
    result = 1 * posinf
    assert result == posinf


def test_neg__mul__():
    result = 1 * neginf
    assert result == neginf


def test_pos__truediv__():
    result = posinf / 2
    assert result == posinf


def test_neg__truediv__():
    result = neginf / 2
    assert result == neginf


def test_pos__rtruediv__():
    result = 1 / posinf
    assert result == 0


def test_neg__rtruediv__():
    result = 1 / neginf
    assert result == 0


def test_pos__floordiv__():
    result = posinf // 2
    assert result == posinf


def test_neg__floordiv__():
    result = neginf // 2
    assert result == neginf


def test_pos__rfloordiv__():
    result = 1 // posinf
    assert result == 0


def test_neg__rfloordiv__():
    result = 1 // neginf
    assert result == 0


def test_pos__mod__():
    result = posinf % 1
    assert result == 0


def test_neg__mod__():
    result = neginf % 1
    assert result == 0


def test_pos__rmod__():
    result = 1 % posinf
    assert result == 1


def test_neg__rmod__():
    result = 1 % neginf
    assert result == 1


def test_pos__divmod__():
    result = divmod(1, posinf)
    assert result == (0, 1)


def test_neg__divmod__():
    result = divmod(1, neginf)
    assert result == (0, 1)     # TODO: Should this be negative?


def test_pos__rdivmod__():
    result = divmod(posinf, 1)
    assert result == (posinf, 0)


def test_neg__rdivmod__():
    result = divmod(neginf, 1)
    assert result == (neginf, 0)


def test_pos__pow__():
    result = posinf ** 2
    assert result == posinf


def test_neg__pow__():
    result = neginf ** 2
    assert result == posinf


def test_pos__rpow__():
    result = 2 ** posinf
    assert result == posinf


def test_neg__rpow__():
    result = 2 ** neginf
    assert result == 0


def test_pos__lshift__():
    result = posinf << 2
    assert result == posinf


def test_neg__lshift__():
    result = neginf << 2
    assert result == neginf


def test_pos__rlshift__():
    result = 2 << posinf
    assert result == posinf


def test_neg__rlshift__():
    result = 2 << neginf
    assert result == 0


def test_pos__rshift__():
    result = posinf >> 2
    assert result == posinf


def test_neg__rshift__():
    result = neginf >> 2
    assert result == neginf


def test_pos__rrshift__():
    result = 2 >> posinf
    assert result == 0


def test_neg__rrshift__():
    result = 2 >> neginf
    assert result == posinf


def test_pos__and__():
    result = posinf & 2
    assert result == 2


def test_neg__and__():
    result = neginf & 2
    assert result == 2


def test_pos__xor__():
    result = posinf ^ 2
    assert result == ~2


def test_neg__xor__():
    result = neginf ^ 2
    assert result == ~2


def test_pos__or__():
    result = posinf | 2
    assert result == posinf


def test_neg__or__():
    result = neginf | 2
    assert result == posinf


def test_pos__neg__():
    result = -posinf
    assert result == neginf


def test_neg__neg__():
    result = -neginf
    assert result == posinf


def test_pos__pos__():
    result = +posinf
    assert result == posinf


def test_neg__pos__():
    result = +neginf
    assert result == neginf


def test_pos__abs__():
    result = abs(posinf)
    assert result == posinf


def test_neg__abs__():
    result = abs(neginf)
    assert result == posinf


def test_pos__invert__():
    result = ~posinf
    assert result == neginf


def test_neg__invert__():
    result = ~neginf
    assert result == posinf


def test_pos__round__():
    result = round(posinf)
    assert result == posinf


def test_neg__round__():
    result = round(neginf)
    assert result == neginf


def test_pos__trunc__():
    result = math.trunc(posinf)
    assert result == posinf


def test_neg__trunc__():
    result = math.trunc(neginf)
    assert result == neginf


def test_pos__floor__():
    result = math.floor(posinf)
    assert result == posinf


def test_neg__floor__():
    result = math.floor(neginf)
    assert result == neginf


def test_pos__ceil__():
    result = math.ceil(posinf)
    assert result == posinf


def test_neg__ceil__():
    result = math.ceil(neginf)
    assert result == neginf
