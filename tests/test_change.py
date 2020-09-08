from sizebot.lib.change import LimitedRate


def test_change():
    LimitedRate.parse("3m/h until 50m")
