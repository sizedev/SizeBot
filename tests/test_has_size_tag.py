from sizebot.lib.utils import hasSizeTag


def test_integer_one_unit():
    val = hasSizeTag("DigiDuncan [1m]")
    assert val is True


def test_integer_one_unit_plus_commas():
    val = hasSizeTag("DigiDuncan [1,000mi]")
    assert val is True


def test_integer_one_long_unit():
    val = hasSizeTag("DigiDuncan [1kuni]")
    assert val is True


def test_integer_one_long_unit_plus_commas():
    val = hasSizeTag("DigiDuncan [1,000Yuni]")
    assert val is True


def test_integer_feet_no_inches():
    val = hasSizeTag("DigiDuncan [5']")
    assert val is True


def test_integer_feet_no_inches_plus_commas():
    val = hasSizeTag("DigiDuncan [5,000']")
    assert val is True


def test_integer_inches():
    val = hasSizeTag("DigiDuncan [8\"]")
    assert val is True


def test_integer_feet_and_inches():
    val = hasSizeTag("DigiDuncan [5'8\"]")
    assert val is True


def test_integer_feet_and_inches_plus_commas():
    val = hasSizeTag("DigiDuncan [5,000'8\"]")
    assert val is True


def test_integer_feet_and_fractional_inches():
    val = hasSizeTag("DigiDuncan [5'8½\"]")
    assert val is True


def test_integer_feet_and_fractional_inches_plus_commas():
    val = hasSizeTag("DigiDuncan [5,000'8½\"]")
    assert val is True


def test_decimal_feet():
    val = hasSizeTag("DigiDuncan [5.8']")
    assert val is True


def test_decimal_inches():
    val = hasSizeTag("DigiDuncan [8.5\"]")
    assert val is True


def test_decimal_feet_and_inches():
    val = hasSizeTag("DigiDuncan [5'8.5\"]")
    assert val is True


def test_decimal_one_unit():
    val = hasSizeTag("DigiDuncan [1.1m]")
    assert val is True


def test_decimal_one_unit_plus_commas():
    val = hasSizeTag("DigiDuncan [1,000mi]")
    assert val is True


def test_decimal_one_long_unit():
    val = hasSizeTag("DigiDuncan [1.1kuni]")
    assert val is True


def test_decimal_one_long_unit_plus_commas():
    val = hasSizeTag("DigiDuncan [1,000.1Yuni]")
    assert val is True


def test_integer_E_pos_no_plus():
    val = hasSizeTag("DigiDuncan [1E10ly]")
    assert val is True


def test_integer_E_pos_plus():
    val = hasSizeTag("DigiDuncan [1E+10ly]")
    assert val is True


def test_integer_E_neg():
    val = hasSizeTag("DigiDuncan [1E-10ly]")
    assert val is True


def test_integer_e_pos_no_plus():
    val = hasSizeTag("DigiDuncan [1e10ly]")
    assert val is True


def test_integer_e_pos_plus():
    val = hasSizeTag("DigiDuncan [1e+10ly]")
    assert val is True


def test_integer_e_neg():
    val = hasSizeTag("DigiDuncan [1e-10ly]")
    assert val is True


def test_decimal_E_pos_no_plus():
    val = hasSizeTag("DigiDuncan [1.1E10ly]")
    assert val is True


def test_decimal_E_pos_plus():
    val = hasSizeTag("DigiDuncan [1.1E+10ly]")
    assert val is True


def test_decimal_E_neg():
    val = hasSizeTag("DigiDuncan [1.1E-10ly]")
    assert val is True


def test_decimal_e_pos_no_plus():
    val = hasSizeTag("DigiDuncan [1.1e10ly]")
    assert val is True


def test_decimal_e_pos_plus():
    val = hasSizeTag("DigiDuncan [1.1e+10ly]")
    assert val is True


def test_decimal_e_neg():
    val = hasSizeTag("DigiDuncan [1.1e-10ly]")
    assert val is True


def test_fractional_inch():
    val = hasSizeTag("DigiDuncan [⅝in]")
    assert val is True


def test_zero():
    val = hasSizeTag("DigiDuncan [0]")
    assert val is True


def test_infinity():
    val = hasSizeTag("DigiDuncan [∞]")
    assert val is True


def test_zalgo():
    val = hasSizeTag("D̶̨i͏̢͟g͞i̴͡D͝ư͢nc͞an̸ [5'8\"]")
    assert val is True


def test_brackets_in_name():
    val = hasSizeTag("[DigiDuncan] [5'8\"]")
    assert val is True


def test_empty_tag():
    val = hasSizeTag("DigiDuncan []")
    assert val is False


def test_three_units():
    val = hasSizeTag("DigiDuncan [5km5m5cm]")
    assert val is False


def test_too_long_unit():
    val = hasSizeTag("DigiDuncan [50nuggets]")
    assert val is False


def test_integer_one_unit_plus_species():
    val = hasSizeTag("DigiDuncan [1m, Species]")
    assert val is True


def test_integer_one_unit_plus_commas_plus_species():
    val = hasSizeTag("DigiDuncan [1,000mi, Species]")
    assert val is True


def test_integer_one_long_unit_plus_species():
    val = hasSizeTag("DigiDuncan [1kuni, Species]")
    assert val is True


def test_integer_one_long_unit_plus_commas_plus_species():
    val = hasSizeTag("DigiDuncan [1,000Yuni, Species]")
    assert val is True


def test_integer_feet_no_inches_plus_species():
    val = hasSizeTag("DigiDuncan [5', Species]")
    assert val is True


def test_integer_feet_no_inches_plus_commas_plus_species():
    val = hasSizeTag("DigiDuncan [5,000', Species]")
    assert val is True


def test_integer_inches_plus_species():
    val = hasSizeTag("DigiDuncan [8\", Species]")
    assert val is True


def test_integer_feet_and_inches_plus_species():
    val = hasSizeTag("DigiDuncan [5'8\", Species]")
    assert val is True


def test_integer_feet_and_inches_plus_commas_plus_species():
    val = hasSizeTag("DigiDuncan [5,000'8\", Species]")
    assert val is True


def test_integer_feet_and_fractional_inches_plus_species():
    val = hasSizeTag("DigiDuncan [5'8½\", Species]")
    assert val is True


def test_integer_feet_and_fractional_inches_plus_commas_plus_species():
    val = hasSizeTag("DigiDuncan [5,000'8½\", Species]")
    assert val is True


def test_decimal_feet_plus_species():
    val = hasSizeTag("DigiDuncan [5.8', Species]")
    assert val is True


def test_decimal_inches_plus_species():
    val = hasSizeTag("DigiDuncan [8.5\", Species]")
    assert val is True


def test_decimal_feet_and_inches_plus_species():
    val = hasSizeTag("DigiDuncan [5'8.5\", Species]")
    assert val is True


def test_decimal_one_unit_plus_species():
    val = hasSizeTag("DigiDuncan [1.1m, Species]")
    assert val is True


def test_decimal_one_unit_plus_commas_plus_species():
    val = hasSizeTag("DigiDuncan [1,000mi, Species]")
    assert val is True


def test_decimal_one_long_unit_plus_species():
    val = hasSizeTag("DigiDuncan [1.1kuni, Species]")
    assert val is True


def test_decimal_one_long_unit_plus_commas_plus_species():
    val = hasSizeTag("DigiDuncan [1,000.1Yuni, Species]")
    assert val is True


def test_integer_E_pos_no_plus_plus_species():
    val = hasSizeTag("DigiDuncan [1E10ly, Species]")
    assert val is True


def test_integer_E_pos_plus_plus_species():
    val = hasSizeTag("DigiDuncan [1E+10ly, Species]")
    assert val is True


def test_integer_E_neg_plus_species():
    val = hasSizeTag("DigiDuncan [1E-10ly, Species]")
    assert val is True


def test_integer_e_pos_no_plus_plus_species():
    val = hasSizeTag("DigiDuncan [1e10ly, Species]")
    assert val is True


def test_integer_e_pos_plus_plus_species():
    val = hasSizeTag("DigiDuncan [1e+10ly, Species]")
    assert val is True


def test_integer_e_neg_plus_species():
    val = hasSizeTag("DigiDuncan [1e-10ly, Species]")
    assert val is True


def test_decimal_E_pos_no_plus_plus_species():
    val = hasSizeTag("DigiDuncan [1.1E10ly, Species]")
    assert val is True


def test_decimal_E_pos_plus_plus_species():
    val = hasSizeTag("DigiDuncan [1.1E+10ly, Species]")
    assert val is True


def test_decimal_E_neg_plus_species():
    val = hasSizeTag("DigiDuncan [1.1E-10ly, Species]")
    assert val is True


def test_decimal_e_pos_no_plus_plus_species():
    val = hasSizeTag("DigiDuncan [1.1e10ly, Species]")
    assert val is True


def test_decimal_e_pos_plus_plus_species():
    val = hasSizeTag("DigiDuncan [1.1e+10ly, Species]")
    assert val is True


def test_decimal_e_neg_plus_species():
    val = hasSizeTag("DigiDuncan [1.1e-10ly, Species]")
    assert val is True


def test_fractional_inch_plus_species():
    val = hasSizeTag("DigiDuncan [⅝in, Species]")
    assert val is True


def test_zero_plus_species():
    val = hasSizeTag("DigiDuncan [0, Species]")
    assert val is True


def test_infinity_plus_species():
    val = hasSizeTag("DigiDuncan [∞, Species]")
    assert val is True


def test_zalgo_plus_species():
    val = hasSizeTag("D̶̨i͏̢͟g͞i̴͡D͝ư͢nc͞an̸ [5'8\", Species]")
    assert val is True


def test_brackets_in_name_plus_species():
    val = hasSizeTag("[DigiDuncan] [5'8\", Species]")
    assert val is True


def test_three_units_plus_species():
    val = hasSizeTag("DigiDuncan [5km5m5cm, Species]")
    assert val is False


def test_too_long_unit_plus_species():
    val = hasSizeTag("DigiDuncan [50nuggets, Species]")
    assert val is False


def no_tag():
    val = hasSizeTag("DigiDuncan")
    assert val is False
