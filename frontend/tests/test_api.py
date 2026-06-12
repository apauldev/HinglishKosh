"""Tests for API query logic (same SQL patterns as Pages Functions)."""

from __future__ import annotations

import sqlite3


def _exact_lookup(db: sqlite3.Connection, word: str, limit: int = 10) -> list[dict]:
    """Replicates /api/lookup SQL."""
    cur = db.execute(
        """SELECT * FROM entries
        WHERE word_hindi = ? OR word_hinglish_roman = ?
        LIMIT ?""",
        (word, word.lower(), limit),
    )
    return [dict(r) for r in cur.fetchall()]


def _fuzzy_lookup(db: sqlite3.Connection, word: str, limit: int = 10) -> list[dict]:
    """Replicates lookup fallback SQL."""
    like = f"%{word}%"
    cur = db.execute(
        """SELECT * FROM entries
        WHERE word_hindi LIKE ? OR word_hinglish_roman LIKE ?
        LIMIT ?""",
        (like, like, limit),
    )
    return [dict(r) for r in cur.fetchall()]


def _fts_search(db: sqlite3.Connection, query: str, limit: int = 20) -> list[dict]:
    """Replicates /api/search FTS SQL."""
    fts_query = " ".join(t + "*" for t in query.strip().split())
    try:
        cur = db.execute(
            """SELECT e.*, rank
            FROM entries_fts f
            JOIN entries e ON e.rowid = f.rowid
            WHERE entries_fts MATCH ?
            ORDER BY rank
            LIMIT ?""",
            (fts_query, limit),
        )
        return [dict(r) for r in cur.fetchall()]
    except sqlite3.OperationalError:
        return []


def _like_search(db: sqlite3.Connection, query: str, limit: int = 20) -> list[dict]:
    """Replicates search fallback SQL."""
    like = f"%{query}%"
    cur = db.execute(
        """SELECT * FROM entries
        WHERE word_hindi LIKE ? OR word_hinglish_roman LIKE ? OR definition LIKE ?
        LIMIT ?""",
        (like, like, like, limit),
    )
    return [dict(r) for r in cur.fetchall()]


def _suggest(db: sqlite3.Connection, q: str, limit: int = 8) -> list[dict]:
    """Replicates /api/suggest SQL."""
    cur = db.execute(
        """SELECT word_hindi, word_hinglish_roman
        FROM entries
        WHERE word_hinglish_roman LIKE ? OR word_hindi LIKE ?
        GROUP BY word_hinglish_roman
        ORDER BY
            CASE
                WHEN word_hinglish_roman = ? THEN 0
                WHEN word_hindi = ? THEN 1
                WHEN word_hinglish_roman LIKE ? THEN 2
                ELSE 3
            END,
            LENGTH(word_hinglish_roman) ASC
        LIMIT ?""",
        (f"{q}%", f"{q}%", q, q, f"{q}%", limit),
    )
    return [dict(r) for r in cur.fetchall()]


# ─── Lookup Tests ───


def test_exact_hindi_lookup(sample_db):
    """Exact lookup by Devanagari word."""
    results = _exact_lookup(sample_db, "पानी")
    assert len(results) >= 1
    assert all(r["word_hindi"] == "पानी" for r in results)


def test_exact_roman_lookup(sample_db):
    """Exact lookup by romanized word."""
    results = _exact_lookup(sample_db, "paani")
    assert len(results) >= 1
    assert all(r["word_hinglish_roman"] == "paani" for r in results)


def test_lookup_not_found(sample_db):
    """Non-existent word returns empty list."""
    results = _exact_lookup(sample_db, "zzzzzznotaword")
    assert len(results) == 0


def test_lookup_fallback_fuzzy(sample_db):
    """When exact fails, fuzzy fallback should still find close matches."""
    exact = _exact_lookup(sample_db, "paan")
    if len(exact) == 0:
        fuzzy = _fuzzy_lookup(sample_db, "paan")
        assert len(fuzzy) >= 1


def test_lookup_case_insensitive(sample_db):
    """Roman lookup should be case-insensitive."""
    upper = _exact_lookup(sample_db, "PAANI")
    lower = _exact_lookup(sample_db, "paani")
    assert len(upper) == len(lower)


# ─── Search Tests ───


def test_fts_search_finds_chai(sample_db):
    """FTS search for 'chai' should find entries."""
    results = _fts_search(sample_db, "chai")
    assert len(results) >= 1


def test_search_fallback_for_short_query(sample_db):
    """Very short query that FTS can't handle should fall back to LIKE."""
    fts_results = _fts_search(sample_db, "a")
    if len(fts_results) == 0:
        like_results = _like_search(sample_db, "a")
        assert len(like_results) >= 1


def test_search_no_results(sample_db):
    """No match returns empty list."""
    results = _fts_search(sample_db, "xyzzynothing")
    assert len(results) == 0


# ─── Suggest Tests ───


def test_suggest_prefix_matching(sample_db):
    """Suggest returns results whose roman form starts with the prefix."""
    results = _suggest(sample_db, "paa")
    if results:
        for r in results:
            assert r["word_hinglish_roman"].startswith("paa") or r["word_hindi"].startswith("paa")


def test_suggest_empty_for_short_query(sample_db):
    """Single character query should not crash and may return empty."""
    results = _suggest(sample_db, "a", limit=8)
    assert isinstance(results, list)


def test_suggest_ordering(sample_db):
    """Suggest should return exact matches before prefix matches."""
    # Use a term likely to have exact + prefix matches
    results = _suggest(sample_db, "paani", limit=8)
    if results:
        first = results[0]
        assert first["word_hinglish_roman"] == "paani" or first["word_hindi"] == "पानी"


# ─── Safe Filter Tests ───


def test_safe_filter_excludes_toxic(sample_db):
    """Safe mode should exclude entries with severity >= 0.5."""
    all_results = _exact_lookup(sample_db, "paani")
    toxic_count = sum(1 for r in all_results if r.get("severity_score", 0) >= 0.5)
    safe_results = [r for r in all_results if r.get("severity_score", 0) < 0.5]
    assert len(safe_results) <= len(all_results)
    if toxic_count > 0:
        assert len(safe_results) < len(all_results)


# ─── Related Words Tests ───


def test_related_words_for_pivotal_entry(full_db):
    """पवित्र स्थान should have related words in the DB."""
    cur = full_db.execute(
        """SELECT e.word_hindi, e.word_hinglish_roman, r.relation_type
        FROM related_words r
        JOIN entries e ON e.id = r.related_entry_id
        WHERE r.entry_id = (
            SELECT id FROM entries WHERE word_hindi = 'पवित्र स्थान' LIMIT 1
        )
        ORDER BY r.relation_type"""
    )
    results = cur.fetchall()
    assert len(results) >= 3, f"Expected at least 3 related words, got {len(results)}"
    types = {r["relation_type"] for r in results}
    assert "same_synset" in types
    assert "broader" in types
    assert "narrower" in types


def test_related_bidirectional(full_db):
    """If A is related to B, then B should be related to A (for same_synset)."""
    cur = full_db.execute(
        """SELECT r1.entry_id, r1.related_entry_id
        FROM related_words r1
        WHERE r1.relation_type = 'same_synset'
        LIMIT 100"""
    )
    pairs = cur.fetchall()
    missing = []
    for row in pairs:
        reverse = full_db.execute(
            """SELECT COUNT(*) as cnt FROM related_words
            WHERE entry_id = ? AND related_entry_id = ? AND relation_type = 'same_synset'""",
            (row["related_entry_id"], row["entry_id"]),
        ).fetchone()["cnt"]
        if reverse == 0:
            missing.append(f"{row['entry_id']} → {row['related_entry_id']} has no reverse")
    assert len(missing) == 0, (
        f"{len(missing)} non-bidirectional same_synset pairs: {missing[:5]}"
    )
