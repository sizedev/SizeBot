from sizebot.lib.utils import stripSizeTag


def test_strip_integer_one_unit():
    val = stripSizeTag("DigiDuncan [1m]")
    assert val == "DigiDuncan"


def test_strip_integer_one_unit_plus_commas():
    val = stripSizeTag("DigiDuncan [1,000mi]")
    assert val == "DigiDuncan"


def test_strip_integer_one_long_unit():
    val = stripSizeTag("DigiDuncan [1kuni]")
    assert val == "DigiDuncan"


def test_strip_integer_one_long_unit_plus_commas():
    val = stripSizeTag("DigiDuncan [1,000Yuni]")
    assert val == "DigiDuncan"


def test_strip_integer_feet_no_inches():
    val = stripSizeTag("DigiDuncan [5']")
    assert val == "DigiDuncan"


def test_strip_integer_feet_no_inches_plus_commas():
    val = stripSizeTag("DigiDuncan [5,000']")
    assert val == "DigiDuncan"


def test_strip_integer_inches():
    val = stripSizeTag("DigiDuncan [8\"]")
    assert val == "DigiDuncan"


def test_strip_integer_feet_and_inches():
    val = stripSizeTag("DigiDuncan [5'8\"]")
    assert val == "DigiDuncan"


def test_strip_integer_feet_and_inches_plus_commas():
    val = stripSizeTag("DigiDuncan [5,000'8\"]")
    assert val == "DigiDuncan"


def test_strip_integer_feet_and_fractional_inches():
    val = stripSizeTag("DigiDuncan [5'8½\"]")
    assert val == "DigiDuncan"


def test_strip_integer_feet_and_fractional_inches_plus_commas():
    val = stripSizeTag("DigiDuncan [5,000'8½\"]")
    assert val == "DigiDuncan"


def test_strip_decimal_feet():
    val = stripSizeTag("DigiDuncan [5.8']")
    assert val == "DigiDuncan"


def test_strip_decimal_inches():
    val = stripSizeTag("DigiDuncan [8.5\"]")
    assert val == "DigiDuncan"


def test_strip_decimal_feet_and_inches():
    val = stripSizeTag("DigiDuncan [5'8.5\"]")
    assert val == "DigiDuncan"


def test_strip_decimal_one_unit():
    val = stripSizeTag("DigiDuncan [1.1m]")
    assert val == "DigiDuncan"


def test_strip_decimal_one_unit_plus_commas():
    val = stripSizeTag("DigiDuncan [1,000mi]")
    assert val == "DigiDuncan"


def test_strip_decimal_one_long_unit():
    val = stripSizeTag("DigiDuncan [1.1kuni]")
    assert val == "DigiDuncan"


def test_strip_decimal_one_long_unit_plus_commas():
    val = stripSizeTag("DigiDuncan [1,000.1Yuni]")
    assert val == "DigiDuncan"


def test_strip_integer_E_pos_no_plus():
    val = stripSizeTag("DigiDuncan [1E10ly]")
    assert val == "DigiDuncan"


def test_strip_integer_E_pos_plus():
    val = stripSizeTag("DigiDuncan [1E+10ly]")
    assert val == "DigiDuncan"


def test_strip_integer_E_neg():
    val = stripSizeTag("DigiDuncan [1E-10ly]")
    assert val == "DigiDuncan"


def test_strip_integer_e_pos_no_plus():
    val = stripSizeTag("DigiDuncan [1e10ly]")
    assert val == "DigiDuncan"


def test_strip_integer_e_pos_plus():
    val = stripSizeTag("DigiDuncan [1e+10ly]")
    assert val == "DigiDuncan"


def test_strip_integer_e_neg():
    val = stripSizeTag("DigiDuncan [1e-10ly]")
    assert val == "DigiDuncan"


def test_strip_decimal_E_pos_no_plus():
    val = stripSizeTag("DigiDuncan [1.1E10ly]")
    assert val == "DigiDuncan"


def test_strip_decimal_E_pos_plus():
    val = stripSizeTag("DigiDuncan [1.1E+10ly]")
    assert val == "DigiDuncan"


def test_strip_decimal_E_neg():
    val = stripSizeTag("DigiDuncan [1.1E-10ly]")
    assert val == "DigiDuncan"


def test_strip_decimal_e_pos_no_plus():
    val = stripSizeTag("DigiDuncan [1.1e10ly]")
    assert val == "DigiDuncan"


def test_strip_decimal_e_pos_plus():
    val = stripSizeTag("DigiDuncan [1.1e+10ly]")
    assert val == "DigiDuncan"


def test_strip_decimal_e_neg():
    val = stripSizeTag("DigiDuncan [1.1e-10ly]")
    assert val == "DigiDuncan"


def test_strip_zero():
    val = stripSizeTag("DigiDuncan [0]")
    assert val == "DigiDuncan"


def test_strip_infinity():
    val = stripSizeTag("DigiDuncan [∞]")
    assert val == "DigiDuncan"


def test_strip_zalgo():
    val = stripSizeTag("D̶̨i͏̢͟g͞i̴͡D͝ư͢nc͞an̸ [5'8\"]")
    assert val == "DigiDuncan"


def test_strip_brackets_in_name():
    val = stripSizeTag("[DigiDuncan] [5'8\"]")
    assert val == "DigiDuncan"


def test_strip_empty_tag():
    val = stripSizeTag("DigiDuncan []")
    assert val == "DigiDuncan []"


def test_strip_three_units():
    val = stripSizeTag("DigiDuncan [5km5m5cm]")
    assert val == "DigiDuncan [5km5m5cm]"


def test_strip_too_long_unit():
    val = stripSizeTag("DigiDuncan [50nuggets]")
    assert val == "DigiDuncan [50nuggets]"
