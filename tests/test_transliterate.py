"""Tests for the transliteration module."""

from src.processing.transliterate import (
    iso_to_hinglish,
    transliterate,
    transliterate_rule_based,
)


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

    def test_schwa_handling(self):
        assert transliterate_rule_based("घर") == "ghar"
        assert transliterate_rule_based("चल") == "chal"
        assert transliterate_rule_based("किताब") == "kitab"

    def test_common_conjuncts(self):
        assert transliterate_rule_based("खड़े") == "khade"
        assert transliterate_rule_based("ज्ञान") == "gyaan"
        assert transliterate_rule_based("शिक्षा") == "shiksha"


class TestTransliterate:
    def test_rule_based_method(self):
        result = transliterate("घर", method="rule_based")
        assert result == "ghar"

    def test_unknown_method_falls_back(self):
        result = transliterate("घर", method="nonexistent")
        assert result == "ghar"

    def test_empty_input(self):
        assert transliterate("") == ""


class TestIsoToHinglish:
    def test_common_iso_forms(self):
        assert iso_to_hinglish("pānī") == "paani"
        assert iso_to_hinglish("mahīna") == "mahina"
        assert iso_to_hinglish("zindagī") == "zindagi"
