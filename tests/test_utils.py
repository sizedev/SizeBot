from sizebot.lib import utils


def test_chunkLines_too_long():
    s = "".join(str(n) for (n) in range(10)) * 10
    result = list(utils.chunkLines(s, 21))
    assert result == ["012345678901234567890", "123456789012345678901", "234567890123456789012", "345678901234567890123", "4567890123456789"]
