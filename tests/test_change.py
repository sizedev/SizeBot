from sizebot.lib.change import Diff


def test_change():
    Diff.parse("+3ft")
