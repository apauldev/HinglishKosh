"""SQLite FTS5 export for high-performance offline dictionary search."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def export_sqlite_fts(
    entries: list[dict[str, Any]],
    output_path: Path,
) -> int:
    """Export dictionary to SQLite with FTS5 virtual table for fast search.

    Creates a database with:
        - dictionary table (full data)
        - dictionary_fts virtual table (full-text search index)

    Args:
        entries: Dictionary entries to export.
        output_path: Path to the .db file.

    Returns:
        Number of entries exported.
    """
    conn = sqlite3.connect(str(output_path))
    cursor = conn.cursor()

    # Create main table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dictionary (
            id TEXT PRIMARY KEY,
            word_hindi TEXT,
            word_hinglish_roman TEXT,
            definition TEXT,
            part_of_speech TEXT,
            example_sentence TEXT,
            source TEXT,
            confidence_score REAL,
            toxicity_flags TEXT,
            severity_score REAL
        )
    """)

    # Create FTS5 virtual table for full-text search
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS dictionary_fts USING fts5(
            word_hindi,
            word_hinglish_roman,
            definition,
            example_sentence,
            content='dictionary',
            content_rowid='rowid'
        )
    """)

    # Insert entries
    count = 0
    for entry in entries:
        # Skip toxic entries from the main search index
        if entry.get("severity_score", 0) >= 0.5:
            continue

        cursor.execute(
            """INSERT OR REPLACE INTO dictionary
               (id, word_hindi, word_hinglish_roman, definition, part_of_speech,
                example_sentence, source, confidence_score, toxicity_flags, severity_score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.get("id", ""),
                entry.get("word_hindi", ""),
                entry.get("word_hinglish_roman", ""),
                entry.get("definition", ""),
                entry.get("part_of_speech", ""),
                entry.get("example_sentence", ""),
                entry.get("source", ""),
                entry.get("confidence_score", 0.0),
                ",".join(entry.get("toxicity_flags", [])),
                entry.get("severity_score", 0.0),
            ),
        )
        count += 1

    # Rebuild FTS index
    cursor.execute("INSERT INTO dictionary_fts(dictionary_fts) VALUES('rebuild')")

    conn.commit()
    conn.close()

    logger.info("Exported %d entries to SQLite FTS5: %s", count, output_path)
    return count


def search_sqlite(
    db_path: Path,
    query: str,
    limit: int = 20,
    safe: bool = False,
) -> list[dict[str, Any]]:
    """Search the SQLite FTS5 index.

    Args:
        db_path: Path to the SQLite database.
        query: Search query (supports FTS5 query syntax).
        limit: Maximum results.
        safe: If True, filter out toxic entries.

    Returns:
        List of matching entries.
    """
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # FTS5 search with ranking
    sql = """
        SELECT d.*, rank
        FROM dictionary_fts fts
        JOIN dictionary d ON fts.rowid = d.rowid
        WHERE dictionary_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """
    params = [query, limit]

    if safe:
        sql = """
            SELECT d.*, rank
            FROM dictionary_fts fts
            JOIN dictionary d ON fts.rowid = d.rowid
            WHERE dictionary_fts MATCH ? AND d.severity_score < 0.5
            ORDER BY rank
            LIMIT ?
        """

    cursor.execute(sql, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return results
