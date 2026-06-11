"""Tests for API and integration modules."""



from src.api.main import _fuzzy_search, create_app
from src.integration.aosp_dict_export import export_aosp_dict, export_words_txt
from src.integration.sqlite_export import export_sqlite_fts, search_sqlite

# === API Tests ===

SAMPLE_ENTRIES = [
    {
        "id": "HIN-00001",
        "word_hindi": "नमस्ते",
        "word_hinglish_roman": "namaste",
        "definition": "A respectful greeting",
        "part_of_speech": "interjection",
        "example_sentence": "नमस्ते, आप कैसे हैं?",
        "source": "WordNet",
        "confidence_score": 0.95,
        "toxicity_flags": [],
        "severity_score": 0.0,
    },
    {
        "id": "HIN-00002",
        "word_hindi": "पानी",
        "word_hinglish_roman": "paani",
        "definition": "Water",
        "part_of_speech": "noun",
        "example_sentence": "पानी पियो",
        "source": "Wiktionary",
        "confidence_score": 0.85,
        "toxicity_flags": [],
        "severity_score": 0.0,
    },
    {
        "id": "HIN-00003",
        "word_hindi": "आग",
        "word_hinglish_roman": "aag",
        "definition": "Fire",
        "part_of_speech": "noun",
        "example_sentence": "आग लगी है",
        "source": "WordNet",
        "confidence_score": 0.95,
        "toxicity_flags": ["profanity"],
        "severity_score": 0.7,
    },
]


class TestFuzzySearch:
    def setup_method(self):
        import src.api.main as api_module
        api_module._dictionary = SAMPLE_ENTRIES

    def test_exact_match_hindi(self):
        results = _fuzzy_search("नमस्ते")
        assert len(results) == 1
        assert results[0]["word_hinglish_roman"] == "namaste"

    def test_exact_match_roman(self):
        results = _fuzzy_search("paani")
        assert len(results) == 1
        assert results[0]["word_hindi"] == "पानी"

    def test_partial_match(self):
        results = _fuzzy_search("pa")
        assert len(results) >= 1  # पानी should match

    def test_no_match(self):
        results = _fuzzy_search("xyz")
        assert results == []

    def test_limit(self):
        results = _fuzzy_search("a", limit=1)
        assert len(results) <= 1


class TestAppCreation:
    def test_app_creates(self):
        app = create_app()
        assert app is not None
        assert app.title == "HinglishKosh API"


# === AOSP Export Tests ===

class TestAospExport:
    def test_export_dict(self, tmp_path):
        output = tmp_path / "test.dict"
        count = export_aosp_dict(SAMPLE_ENTRIES, output)
        assert count == 2  # One entry has severity >= 0.5, should be skipped
        assert output.exists()

    def test_export_words_txt(self, tmp_path):
        output = tmp_path / "words.txt"
        count = export_words_txt(SAMPLE_ENTRIES, output)
        assert count >= 1
        assert output.exists()

        content = output.read_text()
        assert "namaste" in content


# === SQLite Export Tests ===

class TestSqliteExport:
    def test_export_and_search(self, tmp_path):
        db_path = tmp_path / "test.db"
        count = export_sqlite_fts(SAMPLE_ENTRIES, db_path)
        assert count >= 1
        assert db_path.exists()

        # Search for a word
        results = search_sqlite(db_path, "namaste")
        assert len(results) >= 1

    def test_safe_search(self, tmp_path):
        db_path = tmp_path / "test.db"
        export_sqlite_fts(SAMPLE_ENTRIES, db_path)

        # Search with safe filter
        results = search_sqlite(db_path, "aag", safe=True)
        # The "aag" entry has severity 0.7, should be filtered out
        assert all(r["severity_score"] < 0.5 for r in results)

    def test_export_skips_toxic(self, tmp_path):
        db_path = tmp_path / "test.db"
        count = export_sqlite_fts(SAMPLE_ENTRIES, db_path)
        # The toxic entry should be skipped
        assert count == 2
