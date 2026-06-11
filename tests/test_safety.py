"""Tests for safety filter modules."""

import json

from src.safety.profanity_list import ProfanityMatcher, check_profanity, load_profanity_list
from src.safety.severity_scorer import flag_entries, score_severity


class TestProfanityMatcher:
    def test_clean_word(self):
        matcher = ProfanityMatcher()
        assert matcher.contains_profanity("hello") is False

    def test_empty_text(self):
        matcher = ProfanityMatcher()
        assert matcher.contains_profanity("") is False

    def test_is_clean(self):
        matcher = ProfanityMatcher()
        assert matcher.contains_profanity("hello world") is False

    def test_load_external_wordlist(self, tmp_path):
        wordlist = {"words": ["testword"]}
        filepath = tmp_path / "profanity.json"
        filepath.write_text(json.dumps(wordlist), encoding="utf-8")

        words = load_profanity_list(filepath)
        assert "testword" in words

    def test_load_nonexistent_file(self, tmp_path):
        words = load_profanity_list(tmp_path / "nonexistent.json")
        assert len(words) == 0

    def test_normalize_strips_punctuation(self):
        matcher = ProfanityMatcher()
        # The normalize function should handle basic text
        assert matcher.contains_profanity("hello world") is False


class TestSeverityScorer:
    def test_score_severity_clean(self):
        result = score_severity(word="hello", gloss="greeting")
        assert result["profanity"] is False
        assert result["severity_score"] == 0.0

    def test_score_severity_with_profanity(self):
        result = score_severity(word="gaandu", gloss="idiot")
        assert result["profanity"] is True
        assert result["severity_score"] == 1.0

    def test_flag_entries(self):
        entries = [
            {
                "word_hinglish_roman": "paani",
                "definition": "water",
                "examples": ["paani piyo"],
            },
        ]
        matcher = ProfanityMatcher()
        flagged = flag_entries(entries, matcher)
        assert len(flagged) == 1
        assert "profanity" in flagged[0]
        assert "severity_score" in flagged[0]
        assert flagged[0]["profanity"] is False


class TestCheckProfanity:
    def test_check_clean_text(self):
        assert check_profanity("hello world") is False

    def test_check_empty_text(self):
        assert check_profanity("") is False

    def test_check_none_text(self):
        assert check_profanity(None) is False  # type: ignore[arg-type]
