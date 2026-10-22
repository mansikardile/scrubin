from scrubin.validators import luhn_valid, verhoeff_check_digit, verhoeff_valid


def test_verhoeff_roundtrip():
    base = "23456789012"
    num = base + verhoeff_check_digit(base)
    assert verhoeff_valid(num)
    bad = num[:-1] + str((int(num[-1]) + 1) % 10)
    assert not verhoeff_valid(bad)


def test_luhn():
    assert luhn_valid("4111111111111111")
    assert not luhn_valid("4111111111111112")