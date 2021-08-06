from sizebot.lib.digidecimal import Decimal
from sizebot.lib.freefall import freefall


def test_freefall_type():
    t, vel, feelslike = freefall(Decimal(1), Decimal(1), Decimal(1))
    assert isinstance(t, Decimal)
    assert isinstance(vel, Decimal)
    assert isinstance(feelslike, Decimal)
