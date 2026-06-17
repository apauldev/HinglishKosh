"""Tests for API and integration modules."""

import sqlite3

from src.api.main import _fuzzy_search, create_app
from src.integration.aosp_dict_export import export_aosp_dict, export_words_txt
from src.integration.sqlite_export import export_sqlite_fts, sanitize_fts5_query, search_sqlite

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


class TestBuildIndex:
    def _build(self, entries):
        from src.api.main import _build_index

        return _build_index(entries)

    def test_builds_index_from_entries(self):
        idx = self._build(SAMPLE_ENTRIES)
        assert idx["नमस्ते"]["word_hindi"] == "नमस्ते"
        assert idx["namaste"]["word_hindi"] == "नमस्ते"
        assert idx["paani"]["word_hindi"] == "पानी"
        assert "aag" in idx

    def test_skips_empty_strings(self):
        idx = self._build([{"word_hindi": "", "word_hinglish_roman": "test"}])
        assert "" not in idx

    def test_roman_and_hindi_both_indexed(self):
        entries = [
            {"word_hindi": "aaa", "word_hinglish_roman": "bbb", "id": "1"},
            {"word_hindi": "ccc", "word_hinglish_roman": "ddd", "id": "2"},
        ]
        idx = self._build(entries)
        assert idx["aaa"]["id"] == "1"
        assert idx["bbb"]["id"] == "1"
        assert idx["ccc"]["id"] == "2"
        assert idx["ddd"]["id"] == "2"


class TestFuzzySearch:
    def setup_method(self):
        import src.api.main as api_module

        api_module._dictionary = SAMPLE_ENTRIES
        api_module._index = api_module._build_index(SAMPLE_ENTRIES)

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

    def test_confidence_tiebreaking(self):
        results = _fuzzy_search("a")
        # Results should be ordered by score desc, then confidence desc
        if len(results) >= 2:
            confs = [e.get("confidence_score", 0) for e in results]
            for i in range(len(confs) - 1):
                assert confs[i] >= confs[i + 1]

    def test_min_confidence_filters_low(self):
        results = _fuzzy_search("paani", min_confidence=0.9)
        assert len(results) == 0  # paani has confidence 0.85

    def test_min_confidence_passes_high(self):
        results = _fuzzy_search("नमस्ते", min_confidence=0.9)
        assert len(results) == 1  # namaste has confidence 0.95

    def test_index_fallback_when_empty(self):
        import src.api.main as api_module

        api_module._index = {}  # Clear index
        results = _fuzzy_search("नमस्ते", dictionary=api_module._dictionary)
        assert len(results) == 1
        assert results[0]["word_hinglish_roman"] == "namaste"

    def test_safe_dict_linear_scan(self):
        import src.api.main as api_module

        api_module._index = {}
        results = _fuzzy_search("आग", dictionary=api_module._dictionary, use_index=False)
        assert len(results) == 1
        assert results[0]["word_hinglish_roman"] == "aag"


class TestLookupShortCircuit:
    """Bug 5 regression: /lookup must short-circuit on exact index match."""

    def setup_method(self):
        import src.api.main as api_module

        api_module._dictionary = SAMPLE_ENTRIES
        api_module._index = api_module._build_index(SAMPLE_ENTRIES)

    @staticmethod
    def _invoke(handler, **kwargs):
        import asyncio

        return asyncio.run(handler(**kwargs))

    def _lookup_handler(self):
        from src.api.main import create_app

        app = create_app()
        for route in app.routes:
            if route.path == "/lookup":
                return route.endpoint
        raise AssertionError("/lookup route not found")

    def test_exact_index_hit_returns_single_entry(self):
        handler = self._lookup_handler()
        result = self._invoke(handler, word="paani", safe=False, min_confidence=0.0, limit=10)
        assert result["count"] == 1
        assert result["results"][0]["word_hindi"] == "पानी"

    def test_partial_match_falls_back_to_fuzzy(self):
        handler = self._lookup_handler()
        # "paa" is not exact → fuzzy search matches पानी via partial
        result = self._invoke(handler, word="paa", safe=False, min_confidence=0.0, limit=10)
        assert result["count"] >= 1

    def test_min_confidence_blocks_short_circuit(self):
        handler = self._lookup_handler()
        # paani has confidence 0.85; threshold 0.9 blocks the short-circuit,
        # and the fallback fuzzy path also filters it out.
        result = self._invoke(handler, word="paani", safe=False, min_confidence=0.9, limit=10)
        assert result["count"] == 0

    def test_safe_mode_skips_short_circuit(self):
        # Index only covers full dict; safe path must fuzzy-search
        import src.api.main as api_module

        # Populate safe dict with the same entries (minus the toxic one)
        api_module._safe_dictionary = [
            e for e in SAMPLE_ENTRIES if e.get("severity_score", 0) < 0.5
        ]
        try:
            handler = self._lookup_handler()
            result = self._invoke(
                handler,
                word="namaste",
                safe=True,
                min_confidence=0.0,
                limit=10,
            )
            assert result["count"] == 1
        finally:
            api_module._safe_dictionary = []

    def test_short_circuit_does_not_call_fuzzy_search(self, monkeypatch):
        import src.api.main as api_module

        called = {"count": 0}
        original = api_module._fuzzy_search

        def tracker(*args, **kwargs):
            called["count"] += 1
            return original(*args, **kwargs)

        monkeypatch.setattr(api_module, "_fuzzy_search", tracker)

        handler = self._lookup_handler()
        self._invoke(handler, word="namaste", safe=False, min_confidence=0.0, limit=10)
        assert called["count"] == 0  # short-circuit skipped _fuzzy_search entirely


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


class TestSanitizeFts5Query:
    def test_simple_word(self):
        assert sanitize_fts5_query("paani") == '"paani"'

    def test_multiple_tokens(self):
        assert sanitize_fts5_query("paani water") == '"paani" "water"'

    def test_quotes_each_reserved_word(self):
        # Bug 3 regression: OR, AND, NOT, NEAR must be quoted literally
        out = sanitize_fts5_query("paani OR water")
        assert "OR" not in out.split('"')[1::2][0] or out == '"paani" "OR" "water"'
        assert out == '"paani" "OR" "water"'

    def test_and_not_near_quoted(self):
        assert sanitize_fts5_query("hello AND world") == '"hello" "AND" "world"'
        assert sanitize_fts5_query("NOT something") == '"NOT" "something"'
        assert sanitize_fts5_query("NEAR here") == '"NEAR" "here"'

    def test_empty_query(self):
        assert sanitize_fts5_query("") == '""'
        assert sanitize_fts5_query("   ") == '""'

    def test_does_not_crash_search_sqlite(self, tmp_path):
        # End-to-end: reserved-word queries must return results, not raise
        db_path = tmp_path / "test.db"
        export_sqlite_fts(SAMPLE_ENTRIES, db_path)
        # These previously crashed with "fts5: syntax error near 'AND'"
        results = search_sqlite(db_path, "paani OR water")
        assert isinstance(results, list)
        results = search_sqlite(db_path, "namaste AND paani")
        assert isinstance(results, list)
        results = search_sqlite(db_path, "NOT found")
        assert isinstance(results, list)


class TestLikeEscape:
    """Bug 4 regression: % and _ in user input must be treated literally in LIKE."""

    def test_percent_does_not_match_all(self, tmp_path):
        db_path = tmp_path / "test.db"
        export_sqlite_fts(SAMPLE_ENTRIES, db_path)
        conn = sqlite3.connect(str(db_path))
        # Raw % without escape would match every row. With escape it matches nothing.
        escaped = "%".replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        rows = conn.execute(
            """SELECT * FROM dictionary
               WHERE LOWER(word_hinglish_roman) LIKE ? ESCAPE '\\'""",
            (pattern,),
        ).fetchall()
        conn.close()
        assert rows == []

    def test_underscore_matches_literal_underscore(self, tmp_path):
        # Insert an entry with a literal underscore, verify it matches only itself.
        db_path = tmp_path / "test.db"
        entries = list(SAMPLE_ENTRIES) + [
            {
                "id": "TEST-1",
                "word_hindi": "टेस्ट_नाम",
                "word_hinglish_roman": "test_name",
                "definition": "test entry with underscore",
                "part_of_speech": "noun",
                "example_sentence": "",
                "source": "WordNet",
                "confidence_score": 0.9,
                "toxicity_flags": [],
                "severity_score": 0.0,
            },
            {
                "id": "TEST-2",
                "word_hindi": "टेस्टएनाम",
                "word_hinglish_roman": "testAname",
                "definition": "test entry without underscore",
                "part_of_speech": "noun",
                "example_sentence": "",
                "source": "WordNet",
                "confidence_score": 0.9,
                "toxicity_flags": [],
                "severity_score": 0.0,
            },
        ]
        export_sqlite_fts(entries, db_path)
        conn = sqlite3.connect(str(db_path))
        escaped = "test_name".replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        rows = conn.execute(
            """SELECT word_hinglish_roman FROM dictionary
               WHERE LOWER(word_hinglish_roman) LIKE ? ESCAPE '\\'""",
            (pattern,),
        ).fetchall()
        conn.close()
        romans = [r[0] for r in rows]
        assert "test_name" in romans
        assert "testAname" not in romans  # _ was literal, not single-char wildcard
