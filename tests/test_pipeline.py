import pytest

from scrubin import Scrubber
from scrubin.validators import verhoeff_check_digit


def _aadhaar():
    base = "23456789012"
    return base + verhoeff_check_digit(base)


def test_consistent_placeholders():
    out = Scrubber().scrub("a rohan@x.com b rohan@x.com c priya@y.com")
    assert out == "a <EMAIL_1> b <EMAIL_1> c <EMAIL_2>"


def test_full_log_line():
    a = _aadhaar()
    line = (f"ERROR payment failed for user Rohan (rohan.d@gmail.com, +91 98765 43210), "
            f"PAN ABCDE1234F, Aadhaar {a[:4]} {a[4:8]} {a[8:]}, token=abcdef123456XYZ")
    out = Scrubber().scrub(line)
    for ph in ("<EMAIL_1>", "<PHONE_1>", "<PAN_1>", "<AADHAAR_1>", "token=<SECRET_1>"):
        assert ph in out
    assert "rohan.d@gmail.com" not in out and "ABCDE1234F" not in out


def test_random_12_digit_number_is_kept():
    base = "23456789012"
    bad = base + str((int(verhoeff_check_digit(base)) + 1) % 10)  # fails Verhoeff
    assert bad in Scrubber().scrub(f"order {bad} shipped")


def test_same_phone_different_format_same_placeholder():
    out = Scrubber().scrub("call +91 98765 43210 or 9876543210")
    assert out == "call <PHONE_1> or <PHONE_1>"


def test_vault_roundtrip(tmp_path):
    pytest.importorskip("cryptography")
    from scrubin import vault
    s = Scrubber()
    s.scrub("mail rohan@x.com")
    p = str(tmp_path / "m.vault")
    vault.save(s.mapping, p, "pw")
    assert vault.load(p, "pw") == {"<EMAIL_1>": "rohan@x.com"}