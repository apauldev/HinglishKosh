"""Tests for the transliteration module."""

from src.processing.transliterate import transliterate, transliterate_rule_based


class TestTransliterateRuleBased:
    def test_simple_word(self):
        result = transliterate_rule_based("पानी")
        assert result == "paani"  # पा = paa, नी = ni

    def test_common_word(self):
        result = transliterate_rule_based("नमस्ते")
        assert result == "namaste"

    def test_empty_string(self):
        assert transliterate_rule_based("") == ""

    def test_mixed_script(self):
        result = transliterate_rule_based("Hello दुनिया")
        assert "Hello" in result
        assert "duniya" in result

    def test_numbers_preserved(self):
        result = transliterate_rule_based("१२३")
        assert result == "123"

    def test_punctuation_preserved(self):
        result = transliterate_rule_based("नमस्ते!")
        assert "!" in result


class TestTransliterate:
    def test_rule_based_method(self):
        result = transliterate("घर", method="rule_based")
        assert result == "ghar"

    def test_unknown_method_falls_back(self):
        result = transliterate("घर", method="nonexistent")
        assert result == "ghar"

    def test_empty_input(self):
        assert transliterate("") == ""
