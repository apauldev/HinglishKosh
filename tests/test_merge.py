"""Tests for deduplication and merge modules."""

from src.processing.dedup import (
    _normalize_hindi,
    _normalize_roman,
    deduplicate_entries,
)
from src.processing.merge import assign_ids, merge_dictionaries


class TestNormalizeHindi:
    def test_basic(self):
        assert _normalize_hindi("पानी") == "पानी"

    def test_strip_nukta(self):
        # क़ (ka with nukta) should normalize to क
        assert _normalize_hindi("क़") == "क"

    def test_strip_trailing_virama(self):
        # "क्" (with trailing virama) should be stripped
        assert _normalize_hindi("क्") == "क"

    def test_empty(self):
        assert _normalize_hindi("") == ""


class TestNormalizeRoman:
    def test_lowercase(self):
        assert _normalize_roman("Namaste") == "namaste"

    def test_strip_punctuation(self):
        assert _normalize_roman("namaste!") == "namaste"

    def test_collapse_whitespace(self):
        assert _normalize_roman("  paani  ") == "paani"


class TestDeduplication:
    def test_exact_duplicates(self):
        entries = [
            {
                "word_hindi": "पानी",
                "definition": "water",
                "source": "WordNet",
                "word_hinglish_roman": "paani",
                "all_examples": ["पानी पियो"],
            },
            {
                "word_hindi": "पानी",
                "definition": "water",
                "source": "Wiktionary",
                "word_hinglish_roman": "paani",
                "all_examples": ["पानी पियो"],
            },
        ]
        result = deduplicate_entries(entries)
        assert len(result) == 1
        assert "WordNet+Wiktionary" in result[0]["source"]

    def test_different_definitions_same_word(self):
        entries = [
            {
                "word_hindi": "पानी",
                "definition": "water (liquid)",
                "source": "WordNet",
                "word_hinglish_roman": "paani",
                "all_examples": [],
            },
            {
                "word_hindi": "पानी",
                "definition": "water resource",
                "source": "Wiktionary",
                "word_hinglish_roman": "paani",
                "all_examples": [],
            },
        ]
        result = deduplicate_entries(entries)
        assert len(result) == 2  # Different definitions, both kept

    def test_no_duplicates(self):
        entries = [
            {
                "word_hindi": "पानी",
                "definition": "water",
                "source": "WordNet",
                "word_hinglish_roman": "paani",
                "all_examples": [],
            },
            {
                "word_hindi": "आग",
                "definition": "fire",
                "source": "Wiktionary",
                "word_hinglish_roman": "aag",
                "all_examples": [],
            },
        ]
        result = deduplicate_entries(entries)
        assert len(result) == 2

    def test_merges_examples(self):
        entries = [
            {
                "word_hindi": "पानी",
                "definition": "water",
                "source": "WordNet",
                "word_hinglish_roman": "paani",
                "all_examples": ["पानी पियो"],
            },
            {
                "word_hindi": "पानी",
                "definition": "water",
                "source": "Wiktionary",
                "word_hinglish_roman": "paani",
                "all_examples": ["पानी गर्म है"],
            },
        ]
        result = deduplicate_entries(entries)
        assert len(result) == 1
        assert len(result[0]["all_examples"]) == 2


class TestMergeDictionaries:
    def test_merge_with_no_overlap(self):
        wn = [
            {
                "word_hindi": "पानी",
                "word_hinglish_roman": "paani",
                "definition": "water",
                "source": "WordNet",
                "synsets": ["iwn-1"],
                "all_examples": [],
                "confidence_score": 1.0,
            },
        ]
        wk = [
            {
                "word_hindi": "आग",
                "word_hinglish_roman": "aag",
                "definition": "fire",
                "source": "Wiktionary",
                "synsets": [],
                "all_examples": [],
                "confidence_score": 0.85,
            },
        ]
        result = merge_dictionaries(wn, wk)
        assert len(result) == 2

    def test_merge_with_same_definition(self):
        wn = [
            {
                "id": "WN-1",
                "word_hindi": "पानी",
                "word_hinglish_roman": "paani",
                "definition": "water",
                "source": "WordNet",
                "synsets": ["iwn-1"],
                "all_examples": ["पानी पियो"],
                "confidence_score": 1.0,
                "example_sentence": "पानी पियो",
            },
        ]
        wk = [
            {
                "id": "WK-1",
                "word_hindi": "पानी",
                "word_hinglish_roman": "paani",
                "definition": "water",
                "source": "Wiktionary",
                "synsets": [],
                "all_examples": ["drink water"],
                "confidence_score": 0.85,
                "example_sentence": "drink water",
            },
        ]
        result = merge_dictionaries(wn, wk)
        # Should merge: WordNet base + Wiktionary examples/synsets
        assert len(result) == 1
        assert result[0]["source"] == "WordNet"  # WordNet stays as primary
        assert "drink water" in result[0]["all_examples"]

    def test_assigns_ids(self):
        entries = [
            {"word_hindi": "a"},
            {"word_hindi": "b"},
            {"word_hindi": "c"},
        ]
        result = assign_ids(entries)
        assert result[0]["id"] == "HIN-00001"
        assert result[1]["id"] == "HIN-00002"
        assert result[2]["id"] == "HIN-00003"
