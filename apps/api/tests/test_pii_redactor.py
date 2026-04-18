"""Tests for app.utils.pii_redactor — PII pattern stripping for LLM traces."""

from app.utils.pii_redactor import redact


class TestRedactNone:
    def test_none_returns_none(self):
        assert redact(None) is None

    def test_empty_string_returns_empty(self):
        assert redact("") == ""


class TestRedactEmail:
    def test_simple_email(self):
        assert redact("contact user@example.com now") == "contact [EMAIL] now"

    def test_email_with_plus(self):
        assert redact("send to user+tag@gmail.com") == "send to [EMAIL]"

    def test_email_with_dots(self):
        assert redact("first.last@sub.domain.co.uk") == "[EMAIL]"

    def test_multiple_emails(self):
        result = redact("a@b.com and c@d.org")
        assert result.count("[EMAIL]") == 2


class TestRedactPhone:
    def test_international_format(self):
        assert "[PHONE]" in redact("+994-50-123-4567")

    def test_with_parens(self):
        assert "[PHONE]" in redact("+1 (555) 123-4567")

    def test_dotted_format(self):
        assert "[PHONE]" in redact("+44.20.7946.0958")


class TestRedactUUID:
    def test_lowercase_uuid(self):
        result = redact("user 550e8400-e29b-41d4-a716-446655440000 logged in")
        assert "[UUID]" in result
        assert "550e8400" not in result

    def test_uppercase_uuid(self):
        result = redact("ID: 550E8400-E29B-41D4-A716-446655440000")
        assert "[UUID]" in result

    def test_mixed_case_uuid(self):
        result = redact("ref=aB3d8400-E29b-41d4-A716-446655440000")
        assert "[UUID]" in result


class TestRedactCreditCard:
    def test_spaced_card(self):
        assert "[CARD]" in redact("card: 4111 1111 1111 1111")

    def test_dashed_card(self):
        assert "[CARD]" in redact("pay with 4111-1111-1111-1111")

    def test_contiguous_card(self):
        assert "[CARD]" in redact("num 4111111111111111 end")


class TestRedactAzerbaijaniId:
    def test_az_id_card(self):
        assert "[ID]" in redact("document AA1234567")

    def test_az_passport(self):
        assert "[ID]" in redact("passport AZE12345678")

    def test_short_id_not_matched(self):
        result = redact("code AB123")
        assert "[ID]" not in result


class TestRedactMixed:
    def test_all_patterns_in_one_string(self):
        text = (
            "User 550e8400-e29b-41d4-a716-446655440000 "
            "email user@test.com phone +994-50-111-2233 "
            "card 4111 1111 1111 1111 id AA1234567"
        )
        result = redact(text)
        assert "[UUID]" in result
        assert "[EMAIL]" in result
        assert "[PHONE]" in result
        assert "[CARD]" in result
        assert "[ID]" in result
        assert "user@test.com" not in result

    def test_preserves_non_pii_text(self):
        text = "Assessment score is 85.5 for competency leadership"
        assert redact(text) == text

    def test_order_matters_uuid_before_email(self):
        result = redact("550e8400-e29b-41d4-a716-446655440000")
        assert result == "[UUID]"
