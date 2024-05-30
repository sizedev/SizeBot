from sizebot.lib import utils


def test_inttoroman_2020():
    assert utils.int_to_roman(2020) == "MMXX"


def test_inttoroman_1994():
    assert utils.int_to_roman(1994) == "MCMXCIV"


def test_sentence_join():
    assert utils.sentence_join(['red', 'green', 'blue']) == 'red, green and blue'


def test_sentence_join_with_joiner():
    assert utils.sentence_join(['micro', 'tiny', 'normal', 'amazon', 'giantess'], joiner='or') == 'micro, tiny, normal, amazon or giantess'


def test_sentence_join_from_generator():
    assert utils.sentence_join(size for size in ['micro', 'tiny', 'normal', 'amazon', 'giantess']) == 'micro, tiny, normal, amazon and giantess'
