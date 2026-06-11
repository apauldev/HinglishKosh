"""Tests for the Wiktionary loader."""

from __future__ import annotations

import json

import pytest

from src.ingestion.wiktionary_loader import (
    _extract_definition,
    _extract_example,
    _extract_roman,
    load_wiktionary,
    parse_wiktionary_jsonl,
)


def _make_wiktionary_line(
    word: str = "पानी",
    lang_code: str = "hi",
    pos: str = "noun",
    glosses: list | None = None,
    examples: list | None = None,
    forms: list | None = None,
) -> str:
    """Helper to create a valid wiktionary JSONL line."""
    entry = {
        "word": word,
        "lang": "Hindi",
        "lang_code": lang_code,
        "pos": pos,
        "senses": [],
        "forms": forms or [],
    }
    if glosses or examples:
        sense = {"glosses": glosses or [], "tags": []}
        if examples:
            sense["examples"] = examples
        entry["senses"] = [sense]
    return json.dumps(entry, ensure_ascii=False)


class TestExtractRoman:
    def test_with_romanization_form(self):
        forms = [
            {"form": "pani", "tags": ["romanization"]},
            {"form": "पानी", "tags": ["direct", "singular"]},
        ]
        assert _extract_roman(forms) == "pani"

    def test_no_romanization(self):
        forms = [{"form": "पानी", "tags": ["direct"]}]
        result = _extract_roman(forms)
        assert result == ""  # No roman found

    def test_empty_forms(self):
        assert _extract_roman([]) == ""


class TestExtractDefinition:
    def test_from_glosses(self):
        sense = {"glosses": ["water", "H2O"]}
        assert _extract_definition(sense) == "water"

    def test_from_raw_glosses_with_qualifier(self):
        sense = {"raw_glosses": ["(chemistry) water"]}
        assert _extract_definition(sense) == "water"

    def test_empty_sense(self):
        assert _extract_definition({}) == ""


class TestExtractExample:
    def test_from_dict_example(self):
        sense = {
            "examples": [
                {"text": "पानी पियो", "translation": "Drink water"}
            ]
        }
        result = _extract_example(sense)
        assert "पानी पियो" in result
        assert "Drink water" in result

    def test_from_string_example(self):
        sense = {"examples": ["Simple example"]}
        assert _extract_example(sense) == "Simple example"

    def test_no_examples(self):
        assert _extract_example({}) == ""


class TestParseWiktionaryJsonl:
    def test_parse_hindi_entries(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        lines = [
            _make_wiktionary_line(word="पानी", glosses=["water"]),
            _make_wiktionary_line(word="आग", glosses=["fire"]),
            _make_wiktionary_line(word="hello", lang_code="en", glosses=["greeting"]),
        ]
        jsonl_file.write_text("\n".join(lines), encoding="utf-8")

        entries = parse_wiktionary_jsonl(jsonl_file, lang_code="hi")
        assert len(entries) == 2  # Only Hindi entries
        assert entries[0]["word"] == "पानी"

    def test_skip_redirects(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        redirect = json.dumps({"word": "alt", "redirect": "main", "title": "alt"})
        normal = _make_wiktionary_line(word="मुख्य", glosses=["main"])
        jsonl_file.write_text(redirect + "\n" + normal, encoding="utf-8")

        entries = parse_wiktionary_jsonl(jsonl_file)
        assert len(entries) == 1
        assert entries[0]["word"] == "मुख्य"

    def test_handle_malformed_json(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text(
            "not json\n" + _make_wiktionary_line(glosses=["test"]),
            encoding="utf-8",
        )
        entries = parse_wiktionary_jsonl(jsonl_file)
        assert len(entries) == 1


class TestLoadWiktionary:
    def test_load_and_normalize(self, tmp_path):
        jsonl_file = tmp_path / "kaikki-hindi.jsonl"
        entry = {
            "word": "नमस्ते",
            "lang": "Hindi",
            "lang_code": "hi",
            "pos": "interjection",
            "senses": [
                {
                    "glosses": ["a respectful greeting"],
                    "tags": [],
                    "examples": [{"text": "नमस्ते, आप कैसे हैं?"}],
                }
            ],
            "forms": [{"form": "namaste", "tags": ["romanization"]}],
        }
        jsonl_file.write_text(json.dumps(entry, ensure_ascii=False), encoding="utf-8")

        entries = load_wiktionary(tmp_path)
        assert len(entries) == 1

        e = entries[0]
        assert e["word_hindi"] == "नमस्ते"
        assert e["word_hinglish_roman"] == "namaste"
        assert e["definition"] == "a respectful greeting"
        assert e["part_of_speech"] == "interjection"
        assert e["source"] == "Wiktionary"
        assert e["confidence_score"] == 0.85

    def test_missing_directory_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_wiktionary(tmp_path / "nonexistent")
