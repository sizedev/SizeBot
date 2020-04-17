from sizebot.lib import utils


def test_chunkLines_too_long():
    s = "".join(str(n) for (n) in range(10)) * 10
    result = list(utils.chunkLines(s, 21))
    assert result == ["012345678901234567890", "123456789012345678901", "234567890123456789012", "345678901234567890123", "4567890123456789"]


def test_removeBrackets_square():
    s = "[value]"
    result = utils.removeBrackets(s)
    assert result == "value"


def test_removeBrackets_pointy():
    s = "<value>"
    result = utils.removeBrackets(s)
    assert result == "value"


def test_clamp_up():
    assert utils.clamp(10, 1, 20) == 10


def test_clamp_down():
    assert utils.clamp(10, 100, 20) == 20


def test_minmax_correct():
    assert utils.minmax(10, 20) == (10, 20)


def test_minmax_incorrect():
    assert utils.minmax(20, 10) == (10, 20)


def test_minmax_same():
    assert utils.minmax(20, 20) == (20, 20)
