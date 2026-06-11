"""Tests for the WordNet loader."""


import pytest

from src.ingestion.wordnet_loader import (
    _parse_gloss_examples,
    load_english_hindi_linkage,
    load_wordnet,
    parse_synset_file,
)


class TestParseGlossExamples:
    def test_simple_gloss(self):
        gloss, examples = _parse_gloss_examples("a living thing")
        assert gloss == "a living thing"
        assert examples == []

    def test_gloss_with_single_example(self):
        gloss, examples = _parse_gloss_examples('a living thing:"वह एक जीव है"')
        assert gloss == "a living thing"
        assert examples == ["वह एक जीव है"]

    def test_gloss_with_multiple_examples(self):
        raw = 'water:"पानी पियो  /  पानी गर्म है"'
        gloss, examples = _parse_gloss_examples(raw)
        assert gloss == "water"
        assert len(examples) == 2
        assert "पानी पियो" in examples[0]

    def test_empty_input(self):
        gloss, examples = _parse_gloss_examples("")
        assert gloss == ""
        assert examples == []


class TestParseSynsetFile:
    def test_parse_valid_file(self, tmp_path):
        synset_file = tmp_path / "all.hindi"
        synset_file.write_text(
            "100001\tजीव,प्राणी,प्राण\tजीवित चीज़:\"वह एक जीव है\"\tnoun\n"
            "100002\tपानी,जल\tH2O का रासायनिक नाम:\"पानी पियो\"\tnoun\n",
            encoding="utf-8",
        )
        entries = parse_synset_file(synset_file)
        assert len(entries) == 2
        assert entries[0]["synset_id"] == 100001
        assert entries[0]["words"] == ["जीव", "प्राणी", "प्राण"]
        assert entries[0]["pos"] == "noun"
        assert entries[1]["synset_id"] == 100002

    def test_skip_malformed_lines(self, tmp_path):
        synset_file = tmp_path / "all.hindi"
        synset_file.write_text(
            "100001\tजीव\tगloss\tnoun\n"
            "bad_line\n"
            "100002\tपानी\tdefinition\tnoun\n",
            encoding="utf-8",
        )
        entries = parse_synset_file(synset_file)
        assert len(entries) == 2

    def test_empty_file(self, tmp_path):
        synset_file = tmp_path / "all.hindi"
        synset_file.write_text("", encoding="utf-8")
        entries = parse_synset_file(synset_file)
        assert entries == []


class TestLoadWordnet:
    def test_load_from_directory(self, tmp_path):
        synsets_dir = tmp_path / "synsets"
        synsets_dir.mkdir()
        synset_file = synsets_dir / "all.hindi"
        synset_file.write_text(
            "100001\tजीव,प्राणी\tजीवित चीज़:\"वह जीव है\"\tnoun\n"
            "100002\tनमस्ते\tअभिवादन\tinterjection\n",
            encoding="utf-8",
        )

        entries = load_wordnet(tmp_path)
        assert len(entries) == 3  # 2 from synset 100001 (जीव, प्राणी) + 1 from 100002

        # Check schema
        entry = entries[0]
        assert entry["id"] == "WN-100001"
        assert entry["word_hindi"] == "जीव"
        assert entry["source"] == "WordNet"
        assert entry["confidence_score"] == 1.0

    def test_missing_synsets_dir_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_wordnet(tmp_path)


class TestLoadEnglishHindiLinkage:
    def test_load_linkage(self, tmp_path):
        tsv_file = tmp_path / "english-hindi-linked.tsv"
        tsv_file.write_text(
            "# comment line\n"
            "100001\t100001\tliving_thing\tजीव\n"
            "100002\t100002\twater\tपानी\n",
            encoding="utf-8",
        )
        linkage = load_english_hindi_linkage(tsv_file)
        assert linkage[100001] == "living_thing"
        assert linkage[100002] == "water"

    def test_missing_file_returns_empty(self, tmp_path):
        linkage = load_english_hindi_linkage(tmp_path / "nonexistent.tsv")
        assert linkage == {}
