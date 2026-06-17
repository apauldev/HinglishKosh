"""Tests for the dedup/merge logic: definition language classification,
entry merging, quality scoring, and roman-form deduplication."""

from src.processing.pipeline import (
    _classify_definitions,
    _deduplicate_by_roman,
    _definition_lang,
    _entry_quality_score,
    _merge_entries,
)


class TestDefinitionLang:
    def test_hindi_only(self):
        assert _definition_lang("एक प्रकार का फल") == "hi"

    def test_hindi_with_numbers(self):
        assert _definition_lang("१० से अधिक") == "hi"

    def test_english_only(self):
        assert _definition_lang("a type of fruit") == "en"

    def test_english_with_numbers(self):
        assert _definition_lang("10 times more") == "en"

    def test_mixed_hindi_english(self):
        assert _definition_lang("पानी (water)") == "mixed"
        assert _definition_lang("राम (Lord Rama)") == "mixed"

    def test_empty_string(self):
        assert _definition_lang("") == "en"

    def test_punctuation_only(self):
        assert _definition_lang("...") == "en"

    def test_latin_in_hindi_definition(self):
        assert _definition_lang("अंग्रेज़ी भाषा का") == "hi"


class TestEntryQualityScore:
    def test_english_definition_scores_highest(self):
        en_entry = {"definition": "water", "source": "Wiktionary"}
        hi_entry = {"definition": "एक पेय पदार्थ", "source": "WordNet", "example_sentence": "पानी पिओ"}
        en_score = _entry_quality_score(en_entry)
        hi_score = _entry_quality_score(hi_entry)
        assert en_score > hi_score, "English def should score higher than Hindi-only"

    def test_longer_definition_scores_higher(self):
        short = {"definition": "water", "source": "Wiktionary"}
        long = {"definition": "a colorless transparent liquid that forms the seas and rivers", "source": "Wiktionary"}
        assert _entry_quality_score(long) > _entry_quality_score(short)

    def test_wordnet_bonus(self):
        wn = {"definition": "water", "source": "WordNet"}
        wk = {"definition": "water", "source": "Wiktionary"}
        assert _entry_quality_score(wn) > _entry_quality_score(wk)

    def test_example_sentence_bonus(self):
        with_ex = {"definition": "water", "source": "WordNet", "example_sentence": "drink water"}
        without = {"definition": "water", "source": "WordNet"}
        assert _entry_quality_score(with_ex) > _entry_quality_score(without)

    def test_missing_definition_penalty(self):
        empty = {"definition": "", "source": "WordNet"}
        normal = {"definition": "water", "source": "WordNet"}
        assert _entry_quality_score(normal) > _entry_quality_score(empty)

    def test_mixed_lang_scores_between_en_and_hi(self):
        en = {"definition": "water", "source": "Wiktionary"}
        mixed = {"definition": "पानी (water)", "source": "Wiktionary"}
        hi = {"definition": "एक पेय पदार्थ", "source": "Wiktionary"}
        en_score = _entry_quality_score(en)
        mixed_score = _entry_quality_score(mixed)
        hi_score = _entry_quality_score(hi)
        assert en_score > mixed_score > hi_score


class TestMergeEntries:
    def test_merges_sources(self):
        primary = {"definition": "पानी", "source": "WordNet"}
        secondary = {"definition": "water", "source": "Wiktionary"}
        result = _merge_entries(primary, secondary)
        assert result["sources"] == ["WordNet", "Wiktionary"]
        assert result["source"] == "WordNet"

    def test_deduplicates_sources(self):
        primary = {"definition": "पानी", "source": "WordNet"}
        secondary = {"definition": "पानी", "source": "WordNet"}
        result = _merge_entries(primary, secondary)
        assert result["sources"] == ["WordNet"]

    def test_merges_hindi_and_english_definitions(self):
        primary = {"definition": "एक पेय पदार्थ", "source": "WordNet"}
        secondary = {"definition": "water", "source": "Wiktionary"}
        result = _merge_entries(primary, secondary)
        assert result["definition_hi"] == "एक पेय पदार्थ"
        assert result["definition_en"] == "water"

    def test_merges_reverse_order(self):
        primary = {"definition": "water", "source": "Wiktionary"}
        secondary = {"definition": "एक पेय पदार्थ", "source": "WordNet"}
        result = _merge_entries(primary, secondary)
        assert result["definition_en"] == "water"
        assert result["definition_hi"] == "एक पेय पदार्थ"

    def test_merges_synsets(self):
        primary = {"definition": "पानी", "source": "WordNet", "synsets": ["iwn-1"]}
        secondary = {"definition": "water", "source": "Wiktionary", "synsets": ["wk-1"]}
        result = _merge_entries(primary, secondary)
        assert "iwn-1" in result["synsets"]
        assert "wk-1" in result["synsets"]

    def test_deduplicates_synsets(self):
        primary = {"definition": "पानी", "source": "WordNet", "synsets": ["iwn-1"]}
        secondary = {"definition": "water", "source": "Wiktionary", "synsets": ["iwn-1"]}
        result = _merge_entries(primary, secondary)
        assert result["synsets"] == ["iwn-1"]

    def test_merges_examples(self):
        primary = {"definition": "पानी", "source": "WordNet", "all_examples": ["पानी पिओ"]}
        secondary = {"definition": "water", "source": "Wiktionary", "all_examples": ["drink water"]}
        result = _merge_entries(primary, secondary)
        assert "पानी पिओ" in result["all_examples"]
        assert "drink water" in result["all_examples"]

    def test_fills_missing_example_sentence(self):
        primary = {"definition": "पानी", "source": "WordNet"}
        secondary = {"definition": "water", "source": "Wiktionary", "example_sentence": "drink water"}
        result = _merge_entries(primary, secondary)
        assert result["example_sentence"] == "drink water"

    def test_keeps_existing_example_sentence(self):
        primary = {"definition": "पानी", "source": "WordNet", "example_sentence": "पानी पिओ"}
        secondary = {"definition": "water", "source": "Wiktionary", "example_sentence": "drink water"}
        result = _merge_entries(primary, secondary)
        assert result["example_sentence"] == "पानी पिओ"

    def test_merges_pos(self):
        primary = {"definition": "पानी", "source": "WordNet", "part_of_speech": "noun"}
        secondary = {"definition": "water", "source": "Wiktionary"}
        result = _merge_entries(primary, secondary)
        assert result["part_of_speech"] == "noun"

    def test_fills_missing_pos(self):
        primary = {"definition": "पानी", "source": "WordNet"}
        secondary = {"definition": "water", "source": "Wiktionary", "part_of_speech": "noun"}
        result = _merge_entries(primary, secondary)
        assert result["part_of_speech"] == "noun"


class TestDeduplicateByRoman:
    def test_no_duplicates_returns_same(self):
        entries = [
            {"word_hinglish_roman": "paani", "definition": "water", "source": "WordNet"},
            {"word_hinglish_roman": "aag", "definition": "fire", "source": "Wiktionary"},
        ]
        result = _deduplicate_by_roman(entries)
        assert len(result) == 2

    def test_deduplicates_by_roman(self):
        entries = [
            {"word_hinglish_roman": "paani", "definition": "पानी", "source": "WordNet", "example_sentence": "पानी पिओ"},
            {"word_hinglish_roman": "paani", "definition": "water", "source": "Wiktionary"},
        ]
        result = _deduplicate_by_roman(entries)
        assert len(result) == 1

    def test_prefers_english_definition_on_dedup(self):
        entries = [
            {"word_hinglish_roman": "paani", "definition": "पानी", "source": "WordNet", "example_sentence": "पानी पिओ"},
            {"word_hinglish_roman": "paani", "definition": "water", "source": "Wiktionary"},
        ]
        result = _deduplicate_by_roman(entries)
        assert result[0]["definition"] == "water"  # English def wins

    def test_merges_definitions_on_dedup(self):
        entries = [
            {"word_hinglish_roman": "paani", "definition": "पानी", "source": "WordNet", "synsets": ["iwn-1"]},
            {"word_hinglish_roman": "paani", "definition": "water", "source": "Wiktionary", "synsets": ["wk-1"]},
        ]
        result = _deduplicate_by_roman(entries)
        assert result[0].get("definition_hi") == "पानी"
        assert result[0].get("definition_en") == "water"
        assert result[0].get("sources") == ["Wiktionary", "WordNet"]

    def test_no_empty_roman(self):
        entries = [
            {"word_hinglish_roman": "", "definition": "water", "source": "WordNet"},
            {"word_hinglish_roman": "", "definition": "paani", "source": "Wiktionary"},
        ]
        result = _deduplicate_by_roman(entries)
        assert len(result) == 0

    def test_three_way_merge(self):
        entries = [
            {"word_hinglish_roman": "paani", "definition": "पानी", "source": "WordNet", "synsets": ["iwn-1"]},
            {"word_hinglish_roman": "paani", "definition": "water", "source": "Wiktionary", "synsets": ["wk-1"]},
            {"word_hinglish_roman": "paani", "definition": "पानी (water)", "source": "Supplemental", "synsets": ["sup-1"]},
        ]
        result = _deduplicate_by_roman(entries)
        assert len(result) == 1
        assert len(result[0]["sources"]) == 3


class TestClassifyDefinitions:
    def test_classifies_hindi(self):
        entries = [{"definition": "एक प्रकार का फल"}]
        _classify_definitions(entries)
        assert entries[0]["definition_lang"] == "hi"
        assert entries[0]["definition_hi"] == "एक प्रकार का फल"

    def test_classifies_english(self):
        entries = [{"definition": "a type of fruit"}]
        _classify_definitions(entries)
        assert entries[0]["definition_lang"] == "en"
        assert entries[0]["definition_en"] == "a type of fruit"

    def test_classifies_mixed(self):
        entries = [{"definition": "पानी (water)"}]
        _classify_definitions(entries)
        assert entries[0]["definition_lang"] == "mixed"
        assert entries[0]["definition_hi"] == "पानी (water)"
        assert entries[0]["definition_en"] == "पानी (water)"

    def test_preserves_existing_hi_en_fields(self):
        entries = [{"definition": "water", "definition_hi": "पानी", "definition_en": "water"}]
        _classify_definitions(entries)
        assert entries[0]["definition_lang"] == "en"
        assert entries[0]["definition_hi"] == "पानी"
        assert entries[0]["definition_en"] == "water"
