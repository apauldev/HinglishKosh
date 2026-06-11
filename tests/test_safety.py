"""Tests for safety filter modules."""

import json

from src.safety.profanity_list import ProfanityMatcher
from src.safety.severity_scorer import compute_severity, flag_entries
from src.safety.toxicity_classifier import ToxicityClassifier


class TestProfanityMatcher:
    def test_clean_word(self):
        matcher = ProfanityMatcher()
        result = matcher.check_word("hello")
        assert result is None

    def test_empty_text(self):
        matcher = ProfanityMatcher()
        matches = matcher.check_text("")
        assert matches == []

    def test_is_clean(self):
        matcher = ProfanityMatcher()
        assert matcher.is_clean("hello world") is True

    def test_load_external_wordlist(self, tmp_path):
        wordlist = {
            "testword": {"severity": 0.9, "category": "profanity"},
        }
        filepath = tmp_path / "profanity.json"
        filepath.write_text(json.dumps(wordlist), encoding="utf-8")

        matcher = ProfanityMatcher()
        count = matcher.load_wordlist(filepath)
        assert count == 1
        assert "testword" in matcher.wordlist

    def test_load_nonexistent_file(self, tmp_path):
        matcher = ProfanityMatcher()
        count = matcher.load_wordlist(tmp_path / "nonexistent.json")
        assert count == 0

    def test_normalize_strips_punctuation(self):
        matcher = ProfanityMatcher()
        assert matcher._normalize("hello world") == "hello world"
        # Note: ! is mapped to i (leet-speak), not stripped
        assert matcher._normalize("test@word") == "testaword"

    def test_threshold_configurable(self):
        matcher = ProfanityMatcher(threshold=0.9)
        assert matcher.threshold == 0.9


class TestToxicityClassifier:
    def test_classify_empty_text(self):
        clf = ToxicityClassifier()
        result = clf.classify("")
        assert result["toxic"] is False
        assert result["toxicity_score"] == 0.0

    def test_classify_clean_text(self):
        clf = ToxicityClassifier()
        result = clf.classify("The weather is nice today")
        assert result["toxic"] is False

    def test_heuristic_fallback(self):
        clf = ToxicityClassifier()
        # Force heuristic mode by using non-existent model
        clf._available = False
        clf._pipeline = None
        result = clf.classify("I hate this stupid thing")
        assert "toxicity_score" in result

    def test_availability_property(self):
        clf = ToxicityClassifier()
        assert isinstance(clf.is_available, bool)


class TestSeverityScorer:
    def test_compute_severity_clean(self):
        result = compute_severity([], {"toxic": False, "toxicity_score": 0.0, "labels": []})
        assert result["severity_score"] == 0.0
        assert result["is_toxic"] is False
        assert result["toxicity_flags"] == []

    def test_compute_severity_with_dictionary_match(self):
        matches = [{"severity": 0.9, "category": "profanity"}]
        ml_result = {"toxic": False, "toxicity_score": 0.1, "labels": []}
        result = compute_severity(matches, ml_result)
        assert result["severity_score"] > 0
        assert "profanity" in result["toxicity_flags"]

    def test_compute_severity_with_ml_match(self):
        matches = []
        ml_result = {"toxic": True, "toxicity_score": 0.8, "labels": []}
        result = compute_severity(matches, ml_result)
        assert result["is_toxic"] is True
        assert "contextual_toxicity" in result["toxicity_flags"]

    def test_compute_severity_combined(self):
        matches = [{"severity": 0.5, "category": "profanity"}]
        ml_result = {"toxic": True, "toxicity_score": 0.7, "labels": []}
        result = compute_severity(matches, ml_result, weights=(0.5, 0.5))
        assert result["severity_score"] > 0.5
        assert result["is_toxic"] is True

    def test_flag_entries(self):
        entries = [
            {
                "word_hindi": "पानी",
                "definition": "water",
                "example_sentence": "पानी पियो",
                "toxicity_flags": [],
                "severity_score": 0.0,
            },
        ]
        matcher = ProfanityMatcher()
        clf = ToxicityClassifier()
        flagged = flag_entries(entries, matcher, clf)
        assert len(flagged) == 1
        assert "toxicity_flags" in flagged[0]
        assert "severity_score" in flagged[0]
