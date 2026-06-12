"""Shared fixtures for HinglishKosh tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "output"
ENRICHED_JSON = DATA_DIR / "hinglish_dictionary_v1.json"
SCHEMA_SQL = PROJECT_ROOT / "frontend" / "src" / "schema" / "d1.sql"

SAMPLE_SIZE = 1000


def _load_entries() -> list[dict]:
    with open(ENRICHED_JSON, encoding="utf-8") as f:
        data = json.load(f)
    return data["dictionary"]


def _load_schema() -> str:
    return SCHEMA_SQL.read_text()


def _build_sample_db(entries: list[dict], size: int) -> sqlite3.Connection:
    """Build an in-memory SQLite DB from a slice of entries."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(_load_schema())

    # Take a representative sample: mix of sources, POS, with/without synsets
    sample = []
    for source in ("WordNet", "Wiktionary"):
        subset = [e for e in entries if e["source"] == source]
        sample.extend(subset[: size // 4])
    # Fill remaining with entries that have synsets
    with_synsets = [e for e in entries if e.get("synsets") and e not in sample]
    sample.extend(with_synsets[: size - len(sample)])
    # Fill any remaining slots
    if len(sample) < size:
        remainder = [e for e in entries if e not in sample]
        sample.extend(remainder[: size - len(sample)])

    _seed_db(conn, sample)
    return conn


def _build_full_db(entries: list[dict]) -> sqlite3.Connection:
    """Build an in-memory SQLite DB from all entries."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(_load_schema())
    _seed_db(conn, entries)
    return conn


def _seed_db(conn: sqlite3.Connection, entries: list[dict]):
    """Seed the database with entries and related words."""
    for entry in entries:
        conn.execute(
            """INSERT INTO entries (
                id, word_hindi, word_hinglish_roman, definition,
                part_of_speech, example_sentence, source,
                confidence_score, severity_score, toxicity_flags,
                synonyms, antonyms, tags, head_word
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry["id"],
                entry.get("word_hindi", ""),
                entry.get("word_hinglish_roman", ""),
                entry.get("definition", ""),
                entry.get("part_of_speech", ""),
                entry.get("example_sentence", ""),
                entry.get("source", ""),
                entry.get("confidence_score", 0),
                entry.get("severity_score", 0),
                ",".join(entry.get("toxicity_flags", [])),
                ",".join(entry.get("synonyms", [])),
                ",".join(entry.get("antonyms", [])),
                ",".join(entry.get("tags", [])),
                entry.get("head_word", ""),
            ),
        )

        for rel_type, db_col in (
            ("same_synset", "same_synset"),
            ("broader", "broader_terms"),
            ("narrower", "narrower_terms"),
        ):
            for related in entry.get(db_col, []):
                conn.execute(
                    "INSERT OR IGNORE INTO related_words (entry_id, related_entry_id, relation_type) VALUES (?, ?, ?)",
                    (entry["id"], related["id"], rel_type),
                )

    conn.commit()


@pytest.fixture(scope="session")
def all_entries() -> list[dict]:
    return _load_entries()


@pytest.fixture(scope="session")
def full_db(all_entries) -> sqlite3.Connection:
    db = _build_full_db(all_entries)
    yield db
    db.close()


@pytest.fixture(scope="session")
def sample_db(all_entries) -> sqlite3.Connection:
    db = _build_sample_db(all_entries, SAMPLE_SIZE)
    yield db
    db.close()


@pytest.fixture(scope="session")
def sample_entries(all_entries) -> list[dict]:
    """A smaller list of entries for enrichment structure checks."""
    return [e for e in all_entries if e.get("synsets")][:500]
