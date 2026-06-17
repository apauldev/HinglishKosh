"""Tests for the quality audit tool."""

from src.quality.audit import audit_merge_quality

SAMPLE_MERGED = [
    {
        "word_hindi": "पानी",
        "word_hinglish_roman": "paani",
        "definition": "water",
        "sources": ["WordNet", "Wiktionary"],
        "source": "WordNet",
        "definition_hi": "एक पेय पदार्थ",
        "definition_en": "water",
    },
    {
        "word_hindi": "नमस्ते",
        "word_hinglish_roman": "namaste",
        "definition": "greeting",
        "sources": ["WordNet", "Wiktionary"],
        "source": "WordNet",
        "definition_hi": "अभिवादन",
        "definition_en": "greeting",
    },
    {
        "word_hindi": "अजगर",
        "word_hinglish_roman": "ajgar",
        "definition": "python",
        "sources": ["WordNet"],
        "source": "WordNet",
    },
    {
        "word_hindi": "स्वयंभू",
        "word_hinglish_roman": "swayambhu",
        "definition": "self-existent being",
        "sources": ["WordNet", "Wiktionary"],
        "source": "Wiktionary",
        "definition_hi": "स्वयंभू",  # fell back to headword
        "definition_en": "self-existent being",
    },
]


class TestAuditMergeQuality:
    def test_counts_merged_entries(self):
        result = audit_merge_quality(SAMPLE_MERGED)
        assert result["merge_coverage"]["merged_entries"] == 3

    def test_source_pair_distribution(self):
        result = audit_merge_quality(SAMPLE_MERGED)
        pairs = result["merge_coverage"]["source_pair_distribution"]
        assert pairs.get("Wiktionary, WordNet") == 3

    def test_completeness_counts_hi_en(self):
        result = audit_merge_quality(SAMPLE_MERGED)
        comp = result["completeness"]
        # All 3 merged entries have both definition_hi and definition_en in fixtures
        assert comp["has_definition_hi"] == 3
        assert comp["has_definition_en"] == 3
        assert comp["has_both"] == 3

    def test_identical_hi_en_fields_flagged(self):
        # Entry where definition_hi == definition_en
        entries = [
            {
                "word_hindi": "test",
                "word_hinglish_roman": "test",
                "definition": "x",
                "sources": ["WordNet", "Wiktionary"],
                "source": "WordNet",
                "definition_hi": "identical",
                "definition_en": "identical",
            }
        ]
        result = audit_merge_quality(entries)
        assert result["potential_issues"]["identical_hi_and_en"] == 1

    def test_thin_definitions_flagged(self):
        entries = [
            {
                "word_hindi": "x",
                "word_hinglish_roman": "x",
                "definition": "a",  # < 20 chars
                "sources": ["WordNet", "Wiktionary"],
                "source": "WordNet",
                "definition_hi": "x",
                "definition_en": "a",
            }
        ]
        result = audit_merge_quality(entries)
        assert result["potential_issues"]["thin_definition_count"] == 1

    def test_no_merged_entries(self):
        # All single-source: merged count must be 0
        entries = [
            {"word_hindi": "a", "word_hinglish_roman": "a", "source": "WordNet"},
            {"word_hindi": "b", "word_hinglish_roman": "b", "source": "Wiktionary"},
        ]
        result = audit_merge_quality(entries)
        assert result["merge_coverage"]["merged_entries"] == 0
        assert result["completeness"]["hi_pct"] == 0.0
