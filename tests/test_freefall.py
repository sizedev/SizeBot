from sizebot.lib.units import SV, WV, TV, Decimal
from sizebot.lib.freefall import freefall


def test_freefall_type():
    t, vel = freefall(WV(1), SV(1), Decimal(1))
    assert isinstance(t, TV)
    assert isinstance(vel, SV)
