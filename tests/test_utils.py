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


def test_inttoroman_2020():
    assert utils.intToRoman(2020) == "MMXX"


def test_inttoroman_1994():
    assert utils.intToRoman(1994) == "MCMXCIV"


def test_sentence_join():
    assert utils.sentence_join(['red', 'green', 'blue']) == 'red, green and blue'


def test_sentence_join_with_joiner():
    assert utils.sentence_join(['micro', 'tiny', 'normal', 'amazon', 'giantess'], joiner='or') == 'micro, tiny, normal, amazon or giantess'


def test_sentence_join_from_generator():
    assert utils.sentence_join(size for size in ['micro', 'tiny', 'normal', 'amazon', 'giantess']) == 'micro, tiny, normal, amazon and giantess'
