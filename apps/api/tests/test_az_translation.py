"""Unit tests for app.services.az_translation — AZ character guard + translation fallback logic."""

from __future__ import annotations

from app.services.az_translation import _AZ_CHARS, _MIN_AZ_CHAR_RATIO, _has_az_characters


class TestAzCharsSet:
    def test_contains_all_az_specific(self):
        expected = set("əğıöüşçƏĞIÖÜŞÇ")
        assert expected == _AZ_CHARS

    def test_does_not_contain_latin_basics(self):
        for c in "abcdefghijklmnopqrstuvwxyz":
            assert c not in _AZ_CHARS


class TestHasAzCharacters:
    def test_empty_string(self):
        assert _has_az_characters("") is False

    def test_short_text_always_passes(self):
        assert _has_az_characters("salam") is True

    def test_short_text_under_20_chars(self):
        assert _has_az_characters("hello world 12345") is True

    def test_long_text_with_az_chars(self):
        text = "Bu mətn Azərbaycan dilindədir və ğ ı ö ü ş ç simvollarını ehtiva edir"
        assert _has_az_characters(text) is True

    def test_long_text_without_az_chars(self):
        text = "This is a long English text without any Azerbaijani specific characters at all here"
        assert _has_az_characters(text) is False

    def test_exactly_20_chars_no_az(self):
        text = "12345678901234567890"
        assert len(text) == 20
        assert _has_az_characters(text) is False

    def test_19_chars_no_az_passes(self):
        text = "1234567890123456789"
        assert len(text) == 19
        assert _has_az_characters(text) is True

    def test_ratio_boundary(self):
        n = 200
        needed = int(n * _MIN_AZ_CHAR_RATIO)
        text = "a" * (n - needed) + "ə" * needed
        assert _has_az_characters(text) is True

    def test_ratio_just_below(self):
        n = 1000
        needed = int(n * _MIN_AZ_CHAR_RATIO) - 1
        text = "a" * (n - needed) + "ə" * needed
        assert _has_az_characters(text) is False

    def test_all_az_chars(self):
        text = "ə" * 100
        assert _has_az_characters(text) is True

    def test_mixed_case_az_chars(self):
        text = "Ə" * 10 + "Ğ" * 10 + "a" * 80
        assert _has_az_characters(text) is True

    def test_turkish_without_az_specific(self):
        text = "Bu bir uzun Turkce metin ama Azerbaycan karakterleri yok burada hicbir sey yok"
        assert _has_az_characters(text) is False

    def test_russian_text_fails(self):
        text = "Это длинный русский текст без азербайджанских символов и он не должен пройти проверку"
        assert _has_az_characters(text) is False


class TestMinAzCharRatio:
    def test_ratio_value(self):
        assert _MIN_AZ_CHAR_RATIO == 0.005
