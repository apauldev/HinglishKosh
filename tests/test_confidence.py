"""Tests for the confidence scoring formula.

Tests that _compute_confidence produces correct scores from
source, romanization method, multi-source confirmation, and
definition completeness signals.
"""

import pytest

from src.processing.pipeline import (
    _compute_confidence,
    _compute_all_confidence,
    _strip_internal_fields,
)


class TestComputeConfidence:
    def test_wordnet_common_word_is_highest(self):
        entry = {
            "source": "WordNet",
            "sources": ["WordNet"],
            "_romanization_method": "common_word",
            "definition_hi": "पानी",
            "definition_en": "water",
            "example_sentence": "पानी पिओ",
        }
        score = _compute_confidence(entry)
        assert score == pytest.approx(1.0, abs=0.01)

    def test_wiktionary_rule_based_is_lower(self):
        entry = {
            "source": "Wiktionary",
            "sources": ["Wiktionary"],
            "_romanization_method": "rule",
            "definition_en": "water",
        }
        score = _compute_confidence(entry)
        assert score == pytest.approx(0.6568, abs=0.01)

    def test_rule_based_scores_lower_than_common_word(self):
        common_word = {
            "source": "WordNet",
            "sources": ["WordNet"],
            "_romanization_method": "common_word",
            "definition_en": "water",
        }
        rule_based = {
            "source": "WordNet",
            "sources": ["WordNet"],
            "_romanization_method": "rule",
            "definition_en": "water",
        }
        assert _compute_confidence(common_word) > _compute_confidence(rule_based)

    def test_multi_source_boost(self):
        single = {
            "source": "Wiktionary",
            "sources": ["Wiktionary"],
            "_romanization_method": "common_word",
            "definition_en": "water",
        }
        multi = {
            "source": "Wiktionary",
            "sources": ["Wiktionary", "WordNet"],
            "_romanization_method": "common_word",
            "definition_en": "water",
        }
        assert _compute_confidence(multi) > _compute_confidence(single)

    def test_both_definitions_boost(self):
        only_en = {
            "source": "WordNet",
            "sources": ["WordNet"],
            "_romanization_method": "common_word",
            "definition_en": "water",
        }
        both = {
            "source": "WordNet",
            "sources": ["WordNet"],
            "_romanization_method": "common_word",
            "definition_hi": "पानी",
            "definition_en": "water",
        }
        assert _compute_confidence(both) > _compute_confidence(only_en)

    def test_iso_method_scores_between_common_and_rule(self):
        common_word = {
            "source": "WordNet", "sources": ["WordNet"],
            "_romanization_method": "common_word", "definition_en": "water",
        }
        iso = {
            "source": "WordNet", "sources": ["WordNet"],
            "_romanization_method": "iso", "definition_en": "water",
        }
        rule = {
            "source": "WordNet", "sources": ["WordNet"],
            "_romanization_method": "rule", "definition_en": "water",
        }
        cw = _compute_confidence(common_word)
        is_ = _compute_confidence(iso)
        ru = _compute_confidence(rule)
        assert cw > is_ > ru

    def test_toxic_entries_get_floored(self):
        clean = {
            "source": "WordNet", "sources": ["WordNet"],
            "_romanization_method": "common_word",
            "definition_hi": "पानी", "definition_en": "water",
            "severity_score": 0.0,
        }
        toxic = {
            "source": "WordNet", "sources": ["WordNet"],
            "_romanization_method": "common_word",
            "definition_hi": "पानी", "definition_en": "water",
            "severity_score": 1.0,
        }
        clean_score = _compute_confidence(clean)
        toxic_score = _compute_confidence(toxic)
        assert toxic_score <= 0.3
        assert clean_score > toxic_score

    def test_supplemental_source_default(self):
        entry = {
            "source": "some_other",
            "sources": ["some_other"],
            "_romanization_method": "rule",
            "definition_en": "word",
        }
        score = _compute_confidence(entry)
        assert 0.5 < score < 0.8

    def test_unknown_romanization_defaults_to_rule(self):
        entry = {
            "source": "WordNet", "sources": ["WordNet"],
            "definition_en": "water",
        }
        score = _compute_confidence(entry)
        assert 0.6 < score < 0.8

    def test_score_is_capped_at_1(self):
        entry = {
            "source": "WordNet", "sources": ["WordNet", "Wiktionary"],
            "_romanization_method": "common_word",
            "definition_hi": "पानी", "definition_en": "water",
            "example_sentence": "example",
        }
        score = _compute_confidence(entry)
        assert score <= 1.0

    def test_score_is_rounded_to_4_decimal_places(self):
        entry = {
            "source": "WordNet", "sources": ["WordNet"],
            "_romanization_method": "rule",
            "definition_en": "w",
        }
        score = _compute_confidence(entry)
        assert len(str(score).split(".")[1]) <= 4


class TestComputeAllConfidence:
    def test_sets_confidence_on_all_entries(self):
        entries = [
            {"source": "WordNet", "sources": ["WordNet"], "definition_en": "a"},
            {"source": "Wiktionary", "sources": ["Wiktionary"], "definition_en": "b"},
        ]
        _compute_all_confidence(entries)
        for e in entries:
            assert "confidence_score" in e
            assert 0 < e["confidence_score"] <= 1


class TestStripInternalFields:
    def test_removes_internal_fields(self):
        entries = [
            {
                "word_hindi": "पानी",
                "_romanization_method": "common_word",
                "confidence_score": 0.95,
            }
        ]
        _strip_internal_fields(entries)
        assert "_romanization_method" not in entries[0]
        assert "confidence_score" in entries[0]
        assert "word_hindi" in entries[0]
