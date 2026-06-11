"""Main processing pipeline — ties ingestion, processing, and output together.

Usage:
    python -m src.processing.pipeline
    python -m src.processing.pipeline --data-dir data/raw --output-dir data/output
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

from src.ingestion.supplemental_loader import load_supplemental
from src.ingestion.wiktionary_loader import load_wiktionary
from src.ingestion.wordnet_loader import load_english_hindi_linkage, load_wordnet
from src.processing.merge import assign_ids, merge_dictionaries
from src.processing.transliterate import _COMMON_WORDS, iso_to_hinglish, transliterate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _has_devanagari(text: str) -> bool:
    """Check if text contains Devanagari characters."""
    return any("\u0900" <= c <= "\u097f" for c in text)


def _ensure_roman(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert all romanized forms to informal Hinglish.

    - First check _COMMON_WORDS for the Devanagari word
    - Then convert ISO 15919 to informal Hinglish
    - Or transliterate from Devanagari
    """
    for entry in entries:
        hindi = entry.get("word_hindi", "")
        roman = entry.get("word_hinglish_roman", "")

        # First, check if we have a known romanization for this Devanagari word
        if hindi and hindi in _COMMON_WORDS:
            entry["word_hinglish_roman"] = _COMMON_WORDS[hindi]
        elif roman and not _has_devanagari(roman):
            # Already romanized (likely ISO 15919 from Wiktionary) → convert to Hinglish
            entry["word_hinglish_roman"] = iso_to_hinglish(roman)
        elif hindi:
            # Devanagari or missing roman → transliterate from Hindi
            entry["word_hinglish_roman"] = transliterate(hindi)
        elif roman:
            # Has Devanagari in roman field → transliterate
            entry["word_hinglish_roman"] = transliterate(roman)
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
    if linkage_file.exists():
        load_english_hindi_linkage(linkage_file)

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

    # Build safe dataset (filter toxic entries)
    safe_entries = [e for e in merged if e.get("severity_score", 0) < 0.5]
    excluded_entries = [e for e in merged if e.get("severity_score", 0) >= 0.5]

    # Build full dataset
    dataset = {
        "meta": {
            "name": "HinglishKosh (हिंग्लिशकोश)",
            "version": "1.0.0",
            "total_entries": len(merged),
            "safe_entries": len(safe_entries),
            "sources": list(sources.keys()),
            "source_counts": sources,
            "pos_distribution": pos_counts,
            "license": "GPL-3.0",
            "creation_date": date.today().isoformat(),
            "description": (
                "A comprehensive Hinglish-English dictionary dataset for keyboards and apps."
            ),
        },
        "dictionary": merged,
    }

    # Build safe dataset
    safe_dataset = {
        "meta": {
            "name": "HinglishKosh Safe (हिंग्लिशकोश सुरक्षित)",
            "version": "1.0.0",
            "total_entries": len(safe_entries),
            "description": (
                "Safe version of HinglishKosh — toxic entries filtered out (severity_score < 0.5)."
            ),
            **{k: v for k, v in dataset["meta"].items() if k not in ("name", "total_entries")},
        },
        "dictionary": safe_entries,
    }

    # Write full JSON
    output_file = output_dir / "hinglish_dictionary_v1.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    logger.info("Wrote %d entries to %s", len(merged), output_file)

    # Write full compact JSON
    compact_file = output_dir / "hinglish_dictionary_v1.min.json"
    with open(compact_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, separators=(",", ":"))
    logger.info("Wrote compact JSON to %s", compact_file)

    # Write safe JSON
    safe_file = output_dir / "hinglish_dictionary_v1_safe.json"
    with open(safe_file, "w", encoding="utf-8") as f:
        json.dump(safe_dataset, f, ensure_ascii=False, indent=2)
    logger.info("Wrote %d safe entries to %s", len(safe_entries), safe_file)

    # Write safe compact JSON
    safe_compact_file = output_dir / "hinglish_dictionary_v1_safe.min.json"
    with open(safe_compact_file, "w", encoding="utf-8") as f:
        json.dump(safe_dataset, f, ensure_ascii=False, separators=(",", ":"))
    logger.info("Wrote safe compact JSON to %s", safe_compact_file)

    # Write excluded words list
    exclude_file = output_dir / "hinglish_dictionary_v1_excluded.json"
    excluded_words = [
        {
            "word_hindi": e.get("word_hindi", ""),
            "word_hinglish_roman": e.get("word_hinglish_roman", ""),
            "definition": e.get("definition", ""),
            "severity_score": e.get("severity_score", 0),
            "toxicity_flags": e.get("toxicity_flags", []),
            "source": e.get("source", ""),
        }
        for e in excluded_entries
    ]
    with open(exclude_file, "w", encoding="utf-8") as f:
        json.dump(
            {"meta": {"total_excluded": len(excluded_words)}, "excluded": excluded_words},
            f,
            ensure_ascii=False,
            indent=2,
        )
    logger.info("Wrote %d excluded entries to %s", len(excluded_words), exclude_file)

    # Print summary
    print(f"\n{'=' * 60}")
    print("  HinglishKosh (हिंग्लिशकोश) — Pipeline Complete")
    print(f"{'=' * 60}")
    print(f"  Total entries:  {len(merged):,}")
    print(f"  Safe entries:   {len(safe_entries):,} (severity < 0.5)")
    print(f"  Excluded:       {len(excluded_words):,} (severity >= 0.5)")
    print(f"  WordNet:        {sources.get('WordNet', 0):,}")
    print(f"  Wiktionary:     {sources.get('Wiktionary', 0):,}")
    supp_count = sum(v for k, v in sources.items() if k.startswith("supplemental"))
    print(f"  Supplemental:   {supp_count:,}")
    print(f"  Output:         {output_file}")
    print(f"  Safe output:    {safe_file}")
    print(f"  Excluded:       {exclude_file}")
    print(f"{'=' * 60}\n")

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
