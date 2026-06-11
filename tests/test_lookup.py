"""Tests for dictionary lookup — Hindi to Hinglish/English verification."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def dictionary():
    """Load the generated dictionary once for all tests."""
    json_file = Path("data/output/hinglish_dictionary_v1.json")
    if not json_file.exists():
        pytest.skip("Dictionary not generated yet — run pipeline first")
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)
    return data["dictionary"]


@pytest.fixture(scope="module")
def lookup(dictionary):
    """Build a lookup index: Hindi word → best entry (prefer Wiktionary for English defs)."""
    index = {}
    for entry in dictionary:
        word = entry["word_hindi"]
        if word not in index:
            index[word] = entry
        elif entry["source"] == "Wiktionary" and index[word]["source"] == "WordNet":
            index[word] = entry
    return index


class TestDictionaryStructure:
    def test_has_entries(self, dictionary):
        assert len(dictionary) > 100000, f"Expected 100K+ entries, got {len(dictionary)}"

    def test_has_metadata(self, dictionary):
        # Metadata is in the outer dict, not the list — but verify entries have required fields
        entry = dictionary[0]
        required = ["id", "word_hindi", "definition", "source"]
        for field in required:
            assert field in entry, f"Missing required field: {field}"

    def test_entries_from_multiple_sources(self, dictionary):
        sources = set(e["source"] for e in dictionary)
        assert "WordNet" in sources
        assert "Wiktionary" in sources


class TestHindiToHinglishLookup:
    """Verify common Hindi words resolve to correct English definitions."""

    @pytest.mark.parametrize(
        "hindi,expected_english",
        [
            ("पानी", "water"),
            ("घर", "house"),
            ("खाना", "food"),
            ("नमस्ते", "greeting"),
            ("किताब", "book"),
            ("दूध", "milk"),
            ("चाय", "tea"),
            ("मछली", "fish"),
            ("सोना", "gold"),
            ("देश", "country"),
            ("आग", "fire"),
            ("हवा", "air"),
            ("विश्व", "universe"),
            ("केला", "banana"),
            ("सेब", "apple"),
        ],
    )
    def test_hindi_to_english(self, lookup, hindi, expected_english):
        assert hindi in lookup, f"'{hindi}' not found in dictionary"
        entry = lookup[hindi]
        english = entry["definition"].lower()
        assert expected_english.lower() in english, (
            f"'{hindi}' definition '{entry['definition']}' does not contain '{expected_english}'"
        )

    @pytest.mark.parametrize(
        "hindi,expected_roman",
        [
            ("पानी", "paani"),
            ("घर", "ghar"),
            ("नमस्ते", "namaste"),
            ("किताब", "kitab"),
            ("दूध", "doodh"),
            ("चाय", "chai"),
            ("मछली", "machli"),
            ("सोना", "sona"),
            ("आग", "aag"),
            ("हवा", "hawa"),
        ],
    )
    def test_hindi_to_roman(self, lookup, hindi, expected_roman):
        """Test romanized forms (informal Hinglish spelling, no diacritics)."""
        assert hindi in lookup, f"'{hindi}' not found in dictionary"
        roman = lookup[hindi]["word_hinglish_roman"].lower()
        assert roman == expected_roman.lower(), (
            f"'{hindi}' roman '{roman}' does not match expected '{expected_roman}'"
        )

    def test_lookup_returns_pos(self, lookup):
        entry = lookup["पानी"]
        assert entry["part_of_speech"] in ("noun", "Noun", "n")

    def test_lookup_returns_source(self, lookup):
        entry = lookup["पानी"]
        assert entry["source"] in ("WordNet", "Wiktionary")

    def test_nonexistent_word_returns_nothing(self, lookup):
        assert "xyznonexistent" not in lookup
