"""CLI tool for HinglishKosh dictionary lookups.

Usage:
    hinglish-dict lookup namaste
    hinglish-dict search water
    hinglish-dict stats
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _ensure_sqlite_cache(
    data_dir: Path = Path("data/output"),
    safe: bool = False,
    cache_dir: Optional[Path] = None,
) -> Path:
    """Create SQLite cache if it doesn't exist, return path to .db file."""
    if cache_dir is None:
        cache_dir = data_dir
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    suffix = "_safe" if safe else ""
    db_path = cache_dir / f"hinglish_dictionary{suffix}.db"

    if db_path.exists():
        return db_path

    # Build cache from JSON
    json_suffix = "_safe" if safe else ""
    json_file = data_dir / f"hinglish_dictionary{json_suffix}_v1.json"
    if not json_file.exists():
        print(f"Error: Dictionary not found at {json_file}", file=sys.stderr)
        print("Run the pipeline first: python -m src.processing.pipeline", file=sys.stderr)
        sys.exit(1)

    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)
    entries = data.get("dictionary", [])

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
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
    conn.commit()

    for entry in entries:
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

    cursor.execute("INSERT INTO dictionary_fts(dictionary_fts) VALUES('rebuild')")
    conn.commit()
    conn.close()
    print(f"Built SQLite cache: {db_path} ({len(entries)} entries)")
    return db_path


def load_dictionary(data_dir: Path = Path("data/output"), safe: bool = False) -> dict:
    """Load dictionary from JSON file (legacy — kept for stats command)."""
    filename = "hinglish_dictionary_v1_safe.json" if safe else "hinglish_dictionary_v1.json"
    json_file = data_dir / filename
    if not json_file.exists():
        print(f"Error: Dictionary not found at {json_file}", file=sys.stderr)
        print("Run the pipeline first: python -m src.processing.pipeline", file=sys.stderr)
        sys.exit(1)

    with open(json_file, encoding="utf-8") as f:
        return json.load(f)


def cmd_lookup(args):
    """Look up a word in the dictionary."""
    # Use SQLite cache for fast startup
    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    db_path = _ensure_sqlite_cache(Path(args.data_dir), safe=args.safe, cache_dir=cache_dir)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = args.word.lower().strip()
    min_conf = getattr(args, "min_confidence", 0.0)
    results = []

    params: list = [query, query, min_conf, args.limit]
    # Exact match on hindi or roman
    cursor.execute(
        """SELECT * FROM dictionary
           WHERE (LOWER(word_hindi) = ? OR LOWER(word_hinglish_roman) = ?)
           AND confidence_score >= ?
           ORDER BY confidence_score DESC
           LIMIT ?""",
        params,
    )
    results = [dict(row) for row in cursor.fetchall()]

    if not results:
        # Fallback: partial match
        cursor.execute(
            """SELECT * FROM dictionary
               WHERE (LOWER(word_hindi) LIKE ? OR LOWER(word_hinglish_roman) LIKE ?)
               AND confidence_score >= ?
               ORDER BY confidence_score DESC
               LIMIT ?""",
            (f"%{query}%", f"%{query}%", min_conf, args.limit),
        )
        results = [dict(row) for row in cursor.fetchall()]

    conn.close()

    if not results:
        print(f"No results found for: {args.word}")
        return

    for i, entry in enumerate(results, 1):
        print(f"\n{'─' * 50}")
        print(f"  {i}. {entry.get('word_hindi', '')} ({entry.get('word_hinglish_roman', '')})")
        print(f"  POS: {entry.get('part_of_speech', 'N/A')}")
        print(f"  Definition: {entry.get('definition', 'N/A')}")
        if entry.get("example_sentence"):
            print(f"  Example: {entry['example_sentence']}")
        source = entry.get("source", "N/A")
        confidence = entry.get("confidence_score", 0)
        print(f"  Source: {source} | Confidence: {confidence}")
        if entry.get("toxicity_flags"):
            flags = entry["toxicity_flags"].split(",") if isinstance(entry["toxicity_flags"], str) else entry["toxicity_flags"]
            print(f"  Flags: {', '.join(flags)}")

    print(f"\n{'─' * 50}")
    print(f"  {len(results)} result(s) found")


def cmd_search(args):
    """Search the dictionary."""
    # Use SQLite cache for fast startup
    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    db_path = _ensure_sqlite_cache(Path(args.data_dir), safe=args.safe, cache_dir=cache_dir)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = args.query.lower().strip()
    min_conf = getattr(args, "min_confidence", 0.0)

    # FTS5 search with confidence ordering
    cursor.execute(
        """SELECT d.*, rank
           FROM dictionary_fts fts
           JOIN dictionary d ON fts.rowid = d.rowid
           WHERE dictionary_fts MATCH ? AND d.confidence_score >= ?
           ORDER BY rank, d.confidence_score DESC
           LIMIT ?""",
        (query, min_conf, args.limit),
    )
    results = [dict(row) for row in cursor.fetchall()]

    conn.close()

    if not results:
        print(f"No results found for: {args.query}")
        return

    print(f"\nSearch results for: '{args.query}'")
    print(f"{'─' * 50}")

    for i, entry in enumerate(results, 1):
        conf = entry.get("confidence_score", 0)
        print(f"  {i}. {entry.get('word_hindi', '')} ({entry.get('word_hinglish_roman', '')})")
        print(f"     {entry.get('definition', 'N/A')[:80]}  [conf: {conf:.4f}]")

    print(f"\n  {len(results)} result(s)")


def cmd_stats(args):
    """Show dictionary statistics."""
    data = load_dictionary(Path(args.data_dir))
    meta = data.get("meta", {})
    dictionary = data.get("dictionary", [])

    print(f"\n{'═' * 50}")
    print("  HinglishKosh (हिंग्लिशकोश) — Dataset Statistics")
    print(f"{'═' * 50}")
    print(f"  Name:            {meta.get('name', 'N/A')}")
    print(f"  Version:         {meta.get('version', 'N/A')}")
    print(f"  Total entries:   {meta.get('total_entries', len(dictionary)):,}")
    print(f"  License:         {meta.get('license', 'N/A')}")
    print(f"  Created:         {meta.get('creation_date', 'N/A')}")

    source_counts = meta.get("source_counts", {})
    if source_counts:
        print("\n  Sources:")
        for src, count in source_counts.items():
            print(f"    {src}: {count:,}")

    pos_dist = meta.get("pos_distribution", {})
    if pos_dist:
        print("\n  Part of Speech Distribution:")
        for pos, count in sorted(pos_dist.items(), key=lambda x: -x[1]):
            print(f"    {pos}: {count:,}")

    print(f"{'═' * 50}\n")


def main():
    parser = argparse.ArgumentParser(
        prog="hinglish-dict",
        description="HinglishKosh (हिंग्लिशकोश) — Hinglish-English Dictionary CLI",
    )
    parser.add_argument("--data-dir", default="data/output", help="Directory with dictionary data")
    parser.add_argument(
        "--cache-dir", default=None, help="Directory for SQLite cache (default: same as data-dir)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # lookup
    lookup_parser = subparsers.add_parser("lookup", help="Look up a word")
    lookup_parser.add_argument("word", help="Word to look up (Hindi or Roman)")
    lookup_parser.add_argument("--safe", action="store_true", help="Filter toxic entries")
    lookup_parser.add_argument(
        "--min-confidence", type=float, default=0.0, help="Minimum confidence score"
    )
    lookup_parser.add_argument("--limit", type=int, default=10, help="Max results")
    lookup_parser.set_defaults(func=cmd_lookup)

    # search
    search_parser = subparsers.add_parser("search", help="Search the dictionary")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--safe", action="store_true", help="Filter toxic entries")
    search_parser.add_argument(
        "--min-confidence", type=float, default=0.0, help="Minimum confidence score"
    )
    search_parser.add_argument("--limit", type=int, default=20, help="Max results")
    search_parser.set_defaults(func=cmd_search)

    # stats
    stats_parser = subparsers.add_parser("stats", help="Show dictionary statistics")
    stats_parser.set_defaults(func=cmd_stats)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
