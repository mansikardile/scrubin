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


def test_ui_studio_template():
    from scrubin.ui import HTML_TEMPLATE
    assert "ScrubIN" in HTML_TEMPLATE
    assert "/api/scrub" in HTML_TEMPLATE
    assert "Preserve" not in HTML_TEMPLATE


def test_conversational_and_log_secrets():
    s = Scrubber()
    cases = [
        ('{"text": "Hi, this is my password 1234567 "}', '{"text": "Hi, this is my password <SECRET_1> "}'),
        ("Hi, this is my password 1234567.", "Hi, this is my password <SECRET_1>."),
        ("my password is secret123", "my password is <SECRET_1>"),
        ("my password is letmein", "my password is <SECRET_1>"),
        ("the password was changed to Hunter2!", "the password was changed to <SECRET_1>!"),
        ("temporary password 928374", "temporary password <SECRET_1>"),
        ("passcode 482910", "passcode <SECRET_1>"),
        ("pin 1234", "pin <SECRET_1>"),
        ("password 'secret_value'", "password '<SECRET_1>'"),
        ('password "secret_value"', 'password "<SECRET_1>"'),
        ("password secret123", "password <SECRET_1>"),
        ("password=1234567", "password=<SECRET_1>"),
        ("password: 1234567", "password: <SECRET_1>"),
        ("api_key: sk_test_51Mz9999", "api_key: <SECRET_1>"),
        ("api-key=abcdef123456", "api-key=<SECRET_1>"),
        ("client_secret: xyz987654", "client_secret: <SECRET_1>"),
        ("auth_token: tok_12345678", "auth_token: <SECRET_1>"),
        ("authorization: Bearer secret_tok_1234", "authorization: Bearer <SECRET_1>"),
    ]
    for text, expected in cases:
        scrubbed = Scrubber().scrub(text)
        assert "<SECRET_1>" in scrubbed, f"Failed on {text!r}: got {scrubbed!r}"


def test_secrets_negative_cases_no_false_positives():
    s = Scrubber()
    neg_cases = [
        "Please enter your password below",
        "The password should be strong",
        "password policy updated",
        "password reset link sent",
        "password expired yesterday",
        "password manager recommended",
        "token expired at midnight",
        "token invalid error",
        "user has password protection enabled",
        "check your password requirements",
    ]
    for text in neg_cases:
        scrubbed = s.scrub(text)
        assert "<SECRET" not in scrubbed, f"False positive on {text!r}: got {scrubbed!r}"