"""CLI tool for HinglishKosh dictionary lookups.

Usage:
    hinglish-dict lookup namaste
    hinglish-dict search water
    hinglish-dict stats
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_dictionary(data_dir: Path = Path("data/output")) -> dict:
    """Load dictionary from JSON file."""
    json_file = data_dir / "hinglish_dictionary_v1.json"
    if not json_file.exists():
        print(f"Error: Dictionary not found at {json_file}", file=sys.stderr)
        print("Run the pipeline first: python -m src.processing.pipeline", file=sys.stderr)
        sys.exit(1)

    with open(json_file, encoding="utf-8") as f:
        return json.load(f)


def cmd_lookup(args):
    """Look up a word in the dictionary."""
    data = load_dictionary(Path(args.data_dir))
    dictionary = data.get("dictionary", [])

    query = args.word.lower().strip()
    results = []

    for entry in dictionary:
        if (entry.get("word_hindi", "").lower() == query or
            entry.get("word_hinglish_roman", "").lower() == query):
            results.append(entry)

    if not results:
        # Fallback: partial match
        for entry in dictionary:
            if (query in entry.get("word_hindi", "").lower() or
                query in entry.get("word_hinglish_roman", "").lower()):
                results.append(entry)

    if args.safe:
        results = [r for r in results if r.get("severity_score", 0) < 0.5]

    if not results:
        print(f"No results found for: {args.word}")
        return

    for i, entry in enumerate(results[:args.limit], 1):
        print(f"\n{'─' * 50}")
        print(f"  {i}. {entry.get('word_hindi', '')} ({entry.get('word_hinglish_roman', '')})")
        print(f"  POS: {entry.get('part_of_speech', 'N/A')}")
        print(f"  Definition: {entry.get('definition', 'N/A')}")
        if entry.get("example_sentence"):
            print(f"  Example: {entry['example_sentence']}")
        source = entry.get('source', 'N/A')
        confidence = entry.get('confidence_score', 0)
        print(f"  Source: {source} | Confidence: {confidence}")
        if entry.get("toxicity_flags"):
            print(f"  Flags: {', '.join(entry['toxicity_flags'])}")

    print(f"\n{'─' * 50}")
    print(f"  {len(results)} result(s) found")


def cmd_search(args):
    """Search the dictionary."""
    data = load_dictionary(Path(args.data_dir))
    dictionary = data.get("dictionary", [])

    query = args.query.lower().strip()
    results = []

    for entry in dictionary:
        score = 0
        if query in entry.get("word_hindi", "").lower():
            score = 80
        elif query in entry.get("word_hinglish_roman", "").lower():
            score = 75
        elif query in entry.get("definition", "").lower():
            score = 50

        if score > 0:
            results.append((score, entry))

    results.sort(key=lambda x: x[0], reverse=True)

    if args.safe:
        results = [(s, e) for s, e in results if e.get("severity_score", 0) < 0.5]

    results = results[:args.limit]

    if not results:
        print(f"No results found for: {args.query}")
        return

    print(f"\nSearch results for: '{args.query}'")
    print(f"{'─' * 50}")

    for i, (score, entry) in enumerate(results, 1):
        print(f"  {i}. {entry.get('word_hindi', '')} ({entry.get('word_hinglish_roman', '')})")
        print(f"     {entry.get('definition', 'N/A')[:80]}")

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
    parser.add_argument("--data-dir", default="data/output", help="Directory with dictionary JSON")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # lookup
    lookup_parser = subparsers.add_parser("lookup", help="Look up a word")
    lookup_parser.add_argument("word", help="Word to look up (Hindi or Roman)")
    lookup_parser.add_argument("--safe", action="store_true", help="Filter toxic entries")
    lookup_parser.add_argument("--limit", type=int, default=10, help="Max results")
    lookup_parser.set_defaults(func=cmd_lookup)

    # search
    search_parser = subparsers.add_parser("search", help="Search the dictionary")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--safe", action="store_true", help="Filter toxic entries")
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
