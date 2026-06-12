"""Seed a D1-compatible SQLite database from the enriched dataset.

Usage:
    python frontend/src/seed/seed.py
    python frontend/src/seed/seed.py --input data/output/hinglish_dictionary_v1.json --output frontend/hinglishkosh.db
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 1000


def list_to_csv(items: list[str]) -> str:
    return ",".join(items) if items else ""


def seed_database(
    input_path: Path,
    output_path: Path,
    schema_path: Path,
):
    """Create and seed a D1-compatible SQLite database."""
    logger.info("Loading enriched dataset from %s", input_path)
    with open(input_path, encoding="utf-8") as f:
        dataset = json.load(f)

    entries = dataset.get("dictionary", [])
    meta = dataset.get("meta", {})
    logger.info("Loaded %d entries (v%s)", len(entries), meta.get("version", "?"))

    # Remove existing database if present
    if output_path.exists():
        output_path.unlink()
        logger.info("Removed existing database")

    # Create database and schema
    conn = sqlite3.connect(str(output_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("PRAGMA cache_size=-64000")

    logger.info("Creating schema from %s", schema_path)
    schema_sql = schema_path.read_text()
    conn.executescript(schema_sql)
    conn.commit()

    # Insert entries in batches
    insert_sql = """
        INSERT INTO entries (
            id, word_hindi, word_hinglish_roman, definition,
            part_of_speech, example_sentence, source,
            confidence_score, severity_score, toxicity_flags,
            synonyms, antonyms, tags, head_word,
            definition_en, definition_hinglish
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    insert_related_sql = """
        INSERT OR IGNORE INTO related_words (entry_id, related_entry_id, relation_type)
        VALUES (?, ?, ?)
    """

    entry_batch = []
    related_batch = []
    entry_id_set: set[str] = set()

    for i, entry in enumerate(entries):
        entry_id_set.add(entry["id"])
        entry_batch.append((
            entry["id"],
            entry.get("word_hindi", ""),
            entry.get("word_hinglish_roman", ""),
            entry.get("definition", ""),
            entry.get("part_of_speech", ""),
            entry.get("example_sentence", ""),
            entry.get("source", ""),
            entry.get("confidence_score", 0),
            entry.get("severity_score", 0),
            list_to_csv(entry.get("toxicity_flags", [])),
            list_to_csv(entry.get("synonyms", [])),
            list_to_csv(entry.get("antonyms", [])),
            list_to_csv(entry.get("tags", [])),
            entry.get("head_word", ""),
            entry.get("definition_en", ""),
            entry.get("definition_hinglish", ""),
        ))

        # Collect related words
        for rel_type in ("same_synset", "broader_terms", "narrower_terms"):
            for related in entry.get(rel_type, []):
                related_batch.append((
                    entry["id"],
                    related["id"],
                    rel_type.replace("_terms", ""),
                ))

        # Flush batch
        if len(entry_batch) >= BATCH_SIZE:
            conn.executemany(insert_sql, entry_batch)
            entry_batch = []
            if i % 10000 == 0:
                logger.info("  Inserted %d / %d entries...", i + 1, len(entries))

    if entry_batch:
        conn.executemany(insert_sql, entry_batch)

    conn.commit()
    logger.info("Inserted %d entries", len(entries))

    # Filter related words to only those referencing existing entries
    logger.info("Filtering related words (total candidates: %d)", len(related_batch))
    valid_related = [
        r for r in related_batch
        if r[0] in entry_id_set and r[1] in entry_id_set and r[0] != r[1]
    ]

    # Insert related words in batches
    for i in range(0, len(valid_related), BATCH_SIZE):
        batch = valid_related[i : i + BATCH_SIZE]
        conn.executemany(insert_related_sql, batch)

    conn.commit()
    logger.info("Inserted %d related word links", len(valid_related))

    # Run ANALYZE
    conn.execute("ANALYZE")
    conn.commit()

    # Verify
    cursor = conn.execute("SELECT COUNT(*) FROM entries")
    entry_count = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM related_words")
    related_count = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM entries_fts")
    fts_count = cursor.fetchone()[0]

    conn.close()

    db_size = output_path.stat().st_size
    logger.info("=" * 50)
    logger.info("Database created: %s", output_path)
    logger.info("  Size: %.1f MB", db_size / (1024 * 1024))
    logger.info("  Entries: %d", entry_count)
    logger.info("  Related word links: %d", related_count)
    logger.info("  FTS indexed: %d", fts_count)
    logger.info("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Seed D1 database from enriched dataset")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/output/hinglish_dictionary_v1.json"),
        help="Input enriched dataset JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("frontend/hinglishkosh.db"),
        help="Output SQLite database path",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("frontend/src/schema/d1.sql"),
        help="Path to schema SQL file",
    )
    args = parser.parse_args()

    seed_database(
        input_path=args.input,
        output_path=args.output,
        schema_path=args.schema,
    )


if __name__ == "__main__":
    main()
