"""Main processing pipeline — ties ingestion, processing, and output together.

Usage:
    python -m src.processing.pipeline
    python -m src.processing.pipeline --data-dir data/raw --output-dir data/output
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, timezone
from pathlib import Path
from typing import Any

from src.ingestion.supplemental_loader import load_supplemental
from src.ingestion.wiktionary_loader import load_wiktionary
from src.ingestion.wordnet_loader import load_english_hindi_linkage, load_wordnet
from src.processing.merge import assign_ids, merge_dictionaries
from src.processing.transliterate import transliterate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _ensure_roman(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fill in romanized forms for entries missing them."""
    for entry in entries:
        if not entry.get("word_hinglish_roman"):
            entry["word_hinglish_roman"] = transliterate(entry.get("word_hindi", ""))
    return entries


def run_pipeline(
    data_dir: Path = Path("data/raw"),
    output_dir: Path = Path("data/output"),
    include_supplemental: bool = True,
) -> dict[str, Any]:
    """Run the full dictionary processing pipeline.

    Returns metadata about the generated dataset.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # === Stage 1: Load WordNet ===
    logger.info("=== Loading WordNet ===")
    wordnet_dir = data_dir / "wordnet"
    wordnet_entries = []
    if wordnet_dir.exists():
        try:
            wordnet_entries = load_wordnet(wordnet_dir)
            logger.info("Loaded %d WordNet entries", len(wordnet_entries))
        except Exception as e:
            logger.error("Failed to load WordNet: %s", e)

    # Load English-Hindi linkage
    linkage_file = wordnet_dir / "english-hindi-linked.tsv"
    linkage = {}
    if linkage_file.exists():
        linkage = load_english_hindi_linkage(linkage_file)

    # === Stage 2: Load Wiktionary ===
    logger.info("=== Loading Wiktionary ===")
    wiktionary_dir = data_dir / "wiktionary"
    wiktionary_entries = []
    if wiktionary_dir.exists():
        try:
            wiktionary_entries = load_wiktionary(wiktionary_dir)
            logger.info("Loaded %d Wiktionary entries", len(wiktionary_entries))
        except Exception as e:
            logger.error("Failed to load Wiktionary: %s", e)

    # === Stage 3: Load Supplemental ===
    supplemental_entries = []
    if include_supplemental:
        supplemental_dir = data_dir / "supplemental"
        if supplemental_dir.exists():
            logger.info("=== Loading Supplemental Datasets ===")
            supplemental_entries = load_supplemental(supplemental_dir)
            logger.info("Loaded %d supplemental entries", len(supplemental_entries))

    # === Stage 4: Merge ===
    logger.info("=== Merging Dictionaries ===")
    all_entries = wordnet_entries + wiktionary_entries + supplemental_entries
    merged = merge_dictionaries(wordnet_entries, wiktionary_entries + supplemental_entries)

    # Fill in romanized forms
    merged = _ensure_roman(merged)

    # Assign unified IDs
    merged = assign_ids(merged)

    # === Stage 5: Output ===
    logger.info("=== Generating Output ===")

    # Compute stats
    sources = {}
    pos_counts = {}
    for entry in merged:
        src = entry.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1
        pos = entry.get("part_of_speech", "unknown")
        pos_counts[pos] = pos_counts.get(pos, 0) + 1

    # Build output
    dataset = {
        "meta": {
            "name": "HinglishKosh (हिंग्लिशकोश)",
            "version": "1.0.0",
            "total_entries": len(merged),
            "sources": list(sources.keys()),
            "source_counts": sources,
            "pos_distribution": pos_counts,
            "license": "GPL-3.0",
            "creation_date": date.today().isoformat(),
            "description": "A comprehensive Hinglish-English dictionary dataset for keyboards and apps.",
        },
        "dictionary": merged,
    }

    # Write JSON
    output_file = output_dir / "hinglish_dictionary_v1.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    logger.info("Wrote %d entries to %s", len(merged), output_file)

    # Write compact JSON (for production)
    compact_file = output_dir / "hinglish_dictionary_v1.min.json"
    with open(compact_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, separators=(",", ":"))
    logger.info("Wrote compact JSON to %s", compact_file)

    # Print summary
    print(f"\n{'='*60}")
    print(f"  HinglishKosh (हिंग्लिशकोश) — Pipeline Complete")
    print(f"{'='*60}")
    print(f"  Total entries:  {len(merged):,}")
    print(f"  WordNet:        {sources.get('WordNet', 0):,}")
    print(f"  Wiktionary:     {sources.get('Wiktionary', 0):,}")
    print(f"  Supplemental:   {sum(v for k, v in sources.items() if k.startswith('supplemental')):,}")
    print(f"  Output:         {output_file}")
    print(f"{'='*60}\n")

    return dataset["meta"]


def main():
    parser = argparse.ArgumentParser(description="HinglishKosh dictionary pipeline")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/output"))
    parser.add_argument("--no-supplemental", action="store_true")
    args = parser.parse_args()

    run_pipeline(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        include_supplemental=not args.no_supplemental,
    )


if __name__ == "__main__":
    main()
