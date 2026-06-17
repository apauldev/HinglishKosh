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
from src.integration.sqlite_export import export_sqlite_fts
from src.processing.transliterate import (
    _load_common_words,
    iso_to_hinglish,
    transliterate,
    transliterate_rule_based,
)
from src.safety.profanity_list import ProfanityMatcher
from src.safety.severity_scorer import flag_entries

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _has_devanagari(text: str) -> bool:
    """Check if text contains Devanagari characters."""
    return any("\u0900" <= c <= "\u097f" for c in text)


def _definition_lang(definition: str) -> str:
    """Classify definition language: 'hi' (Hindi-only), 'en' (English-only), 'mixed'.

    A definition is Hindi-only if it contains Devanagari characters
    and no ASCII letters. English-only if it has ASCII letters and no
    Devanagari. Mixed if it has both.
    """
    if not definition:
        return "en"
    has_dev = any("\u0900" <= c <= "\u097f" for c in definition)
    has_latin = any(c.isascii() and c.isalpha() for c in definition)
    if has_dev and has_latin:
        return "mixed"
    if has_dev:
        return "hi"
    return "en"


def _ensure_roman(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert all romanized forms to informal Hinglish.

    Priority:
    1. _COMMON_WORDS lookup for the Devanagari word
    2. Transliterate from Devanagari (always preferred over existing roman)
    3. Convert existing roman (ISO 15919) to Hinglish as fallback

    Sets _romanization_method on each entry for downstream confidence scoring.
    """
    common = _load_common_words()
    for entry in entries:
        hindi = entry.get("word_hindi", "")
        roman = entry.get("word_hinglish_roman", "")

        # First, check if we have a known romanization for this Devanagari word
        if hindi and hindi in common:
            entry["word_hinglish_roman"] = common[hindi]
            entry["_romanization_method"] = "common_word"
        elif hindi:
            # Always prefer transliterating from Devanagari
            entry["word_hinglish_roman"] = transliterate(hindi)
            entry["_romanization_method"] = "rule"
        elif roman and not _has_devanagari(roman):
            # No Hindi word, but has roman → convert ISO to Hinglish
            entry["word_hinglish_roman"] = iso_to_hinglish(roman)
            entry["_romanization_method"] = "iso"
        elif roman:
            # Has Devanagari in roman field → transliterate
            entry["word_hinglish_roman"] = transliterate(roman)
            entry["_romanization_method"] = "rule"
    return entries


def _transliterate_definitions(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Transliterate Hindi definitions and example sentences to Hinglish.

    Adds definition_hinglish field with romanized version of the Hindi definition.
    """
    for entry in entries:
        definition = entry.get("definition", "")
        example = entry.get("example_sentence", "")

        # Transliterate definition if it contains Devanagari
        if definition and _has_devanagari(definition):
            entry["definition_hinglish"] = transliterate_rule_based(definition)
        elif definition:
            # Already romanized - use as-is or convert from ISO
            if _has_devanagari(definition):
                entry["definition_hinglish"] = definition
            else:
                entry["definition_hinglish"] = iso_to_hinglish(definition)

        # Transliterate example sentence if it contains Devanagari
        if example and _has_devanagari(example):
            entry["example_hinglish"] = transliterate_rule_based(example)

    return entries


def _merge_entries(primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, Any]:
    """Merge secondary entry's data into primary when both share the same roman form.

    Merges definitions, synsets, examples, and source tracking.
    Primary keeps its core fields (word_hindi, part_of_speech, etc.);
    secondary's unique data is folded in.
    """
    # Merge source tracking
    primary_sources = primary.get("sources", [primary.get("source", "unknown")])
    secondary_sources = secondary.get("sources", [secondary.get("source", "unknown")])
    combined_sources = list(dict.fromkeys(primary_sources + secondary_sources))
    primary["sources"] = combined_sources
    primary["source"] = combined_sources[0]

    # Merge definitions: classify both, fill in hi/en fields
    p_def = primary.get("definition", "")
    s_def = secondary.get("definition", "")
    p_lang = _definition_lang(p_def)
    s_lang = _definition_lang(s_def)

    if p_lang in ("hi", "mixed") or s_lang in ("hi", "mixed"):
        if p_lang in ("hi", "mixed"):
            primary["definition_hi"] = p_def
        elif "definition_hi" not in primary:
            primary["definition_hi"] = s_def

    if p_lang in ("en", "mixed") or s_lang in ("en", "mixed"):
        if p_lang in ("en", "mixed"):
            primary["definition_en"] = p_def
        elif "definition_en" not in primary:
            primary["definition_en"] = s_def

    # Merge synsets
    primary_synsets = primary.get("synsets", [])
    for s in secondary.get("synsets", []):
        if s not in primary_synsets:
            primary_synsets.append(s)
    primary["synsets"] = primary_synsets

    # Merge examples
    primary_examples = primary.get("all_examples", [])
    for ex in secondary.get("all_examples", []):
        if ex and ex not in primary_examples:
            primary_examples.append(ex)
    primary["all_examples"] = primary_examples
    if not primary.get("example_sentence") and secondary.get("example_sentence"):
        primary["example_sentence"] = secondary["example_sentence"]

    # Merge POS if missing
    if not primary.get("part_of_speech") and secondary.get("part_of_speech"):
        primary["part_of_speech"] = secondary["part_of_speech"]

    return primary


def _entry_quality_score(entry: dict[str, Any]) -> int:
    """Score an entry's quality for deduplication ranking.

    Higher score = better entry to keep as primary. Factors:
    - English definitions are more useful (heavy bonus)
    - WordNet source preferred
    - Has example sentence
    - Longer definition
    - Penalty for missing definition
    """
    score = 0
    definition = entry.get("definition", "")

    # Bonus for English definitions (more useful for keyboard users)
    lang = _definition_lang(definition)
    if lang == "en":
        score += 200
    elif lang == "mixed":
        score += 100

    # Longer definition = more detailed
    score += len(definition)

    # WordNet preferred
    if entry.get("source") == "WordNet":
        score += 100

    # Has example sentence
    if entry.get("example_sentence"):
        score += 50

    # Heavy penalty for missing definition
    if not definition:
        score -= 500

    return score


def _deduplicate_by_roman(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate entries by word_hinglish_roman, merging data from dupes.

    When two entries share the same roman form, the higher-quality entry
    is kept as primary; the other's definitions, synsets, and examples
    are merged into it (so no data is lost).
    """
    seen: dict[str, dict[str, Any]] = {}

    for entry in entries:
        roman = entry.get("word_hinglish_roman", "")
        if not roman:
            continue

        if roman not in seen:
            seen[roman] = entry
            continue

        existing = seen[roman]
        existing_score = _entry_quality_score(existing)
        new_score = _entry_quality_score(entry)

        if new_score > existing_score:
            _merge_entries(entry, existing)
            seen[roman] = entry
        else:
            _merge_entries(existing, entry)

    result = list(seen.values())
    logger.info(
        "Deduplicated %d → %d entries by roman form",
        len(entries),
        len(result),
    )
    return result


def _classify_definitions(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Classify each entry's definition language and fill hi/en fields."""
    for entry in entries:
        defn = entry.get("definition", "")
        lang = _definition_lang(defn)
        entry["definition_lang"] = lang
        if lang == "hi" and "definition_hi" not in entry:
            entry["definition_hi"] = defn
        elif lang == "en" and "definition_en" not in entry:
            entry["definition_en"] = defn
        elif lang == "mixed":
            if "definition_hi" not in entry:
                entry["definition_hi"] = defn
            if "definition_en" not in entry:
                entry["definition_en"] = defn
    return entries


def _compute_confidence(entry: dict[str, Any]) -> float:
    """Compute a per-entry confidence score based on source, romanization,
    multi-source confirmation, and definition completeness.

    Formula: base × romanization_mult × source_boost × completeness_mult
    Capped at [0, 1]. Severity >= 0.5 floors the score to <= 0.3.
    """
    source = entry.get("source", "")
    base = {"WordNet": 0.95, "Wiktionary": 0.85}.get(source, 0.70)

    method = entry.get("_romanization_method", "rule")
    roman_mult = {"common_word": 1.0, "iso": 0.92, "rule": 0.75}.get(method, 0.85)

    sources = entry.get("sources", [source])
    num_sources = len(set(sources))
    source_boost = 1.0 + (0.03 * (num_sources - 1))

    defn_hi = entry.get("definition_hi", "")
    defn_en = entry.get("definition_en", "")
    has_example = bool(entry.get("example_sentence"))

    completeness_mult = 1.0
    if defn_hi and defn_en:
        completeness_mult = 1.05
    elif defn_en:
        completeness_mult = 1.03
    elif defn_hi and has_example:
        completeness_mult = 1.02

    score = base * roman_mult * source_boost * completeness_mult

    if entry.get("severity_score", 0) >= 0.5:
        score = min(score, 0.3)

    return round(min(max(score, 0.0), 1.0), 4)


def _compute_all_confidence(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute and set confidence_score for every entry."""
    for entry in entries:
        entry["confidence_score"] = _compute_confidence(entry)
    return entries


_INTERNAL_FIELDS = frozenset({"_romanization_method"})


def _strip_internal_fields(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove internal-only fields before writing output."""
    for entry in entries:
        for field in _INTERNAL_FIELDS:
            entry.pop(field, None)
    return entries


def run_pipeline(
    data_dir: Path = Path("data/raw"),
    output_dir: Path = Path("data/output"),
    include_supplemental: bool = True,
    skip_safety: bool = False,
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

    # Transliterate definitions and examples
    logger.info("=== Transliterating Definitions ===")
    merged = _transliterate_definitions(merged)

    # Assign unified IDs
    merged = assign_ids(merged)

    # Deduplicate by word_hinglish_roman (keep best definition per word)
    merged = _deduplicate_by_roman(merged)

    # Classify definitions and fill hi/en fields
    merged = _classify_definitions(merged)

    # Compute per-entry confidence scores
    logger.info("=== Computing Confidence Scores ===")
    merged = _compute_all_confidence(merged)

    # === Stage 5: Safety Filter ===
    if not skip_safety:
        logger.info("=== Running Safety Filter ===")
        profanity_matcher = ProfanityMatcher()
        logger.info(
            "Safety filter ready (profanity: %s)",
            "loaded" if profanity_matcher.wordlist else "empty",
        )
        merged = flag_entries(merged, profanity_matcher)
        flagged_count = sum(1 for e in merged if e.get("severity_score", 0) >= 0.5)
        logger.info("Safety filter complete: %d entries flagged", flagged_count)
    else:
        logger.info("=== Safety Filter Skipped ===")

    # === Stage 6: Output ===
    logger.info("=== Generating Output ===")

    # Strip internal-only fields before writing
    merged = _strip_internal_fields(merged)

    # Compute stats
    sources = {}
    pos_counts = {}
    multi_source = 0
    hi_only = 0
    en_only = 0
    mixed = 0
    confidence_buckets: dict[str, int] = {}
    for entry in merged:
        src = entry.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1
        pos = entry.get("part_of_speech", "unknown")
        pos_counts[pos] = pos_counts.get(pos, 0) + 1
        if len(entry.get("sources", [src])) > 1:
            multi_source += 1
        lang = entry.get("definition_lang", "en")
        if lang == "hi":
            hi_only += 1
        elif lang == "en":
            en_only += 1
        else:
            mixed += 1
        c = entry.get("confidence_score", 0)
        bucket = f"{c:.2f}"
        confidence_buckets[bucket] = confidence_buckets.get(bucket, 0) + 1

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
            "multi_source_entries": multi_source,
            "definition_languages": {
                "hi_only": hi_only,
                "en_only": en_only,
                "mixed": mixed,
            },
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

    # Export SQLite FTS5 database for fast CLI/API startup
    db_file = output_dir / "hinglish_dictionary_v1.db"
    export_sqlite_fts(merged, db_file)
    logger.info("Exported %d entries to SQLite FTS5: %s", len(safe_entries), db_file)

    # Print summary
    multi_src = sum(1 for e in merged if len(e.get("sources", [e.get("source", "")])) > 1)
    hi_count = sum(1 for e in merged if e.get("definition_lang") == "hi")
    en_count = sum(1 for e in merged if e.get("definition_lang") == "en")
    mixed_count = sum(1 for e in merged if e.get("definition_lang") == "mixed")
    print(f"\n{'=' * 60}")
    print("  HinglishKosh (हिंग्लिशकोश) — Pipeline Complete")
    print(f"{'=' * 60}")
    print(f"  Total entries:      {len(merged):>8,}")
    print(f"  Safe entries:       {len(safe_entries):>8,} (severity < 0.5)")
    print(f"  Excluded:           {len(excluded_words):>8,} (severity >= 0.5)")
    print(f"  Multi-source:       {multi_src:>8,}")
    print(f"  Definitions:")
    print(f"    Hindi-only:       {hi_count:>8,}")
    print(f"    English-only:     {en_count:>8,}")
    print(f"    Mixed:            {mixed_count:>8,}")
    print(f"  WordNet:            {sources.get('WordNet', 0):>8,}")
    print(f"  Wiktionary:         {sources.get('Wiktionary', 0):>8,}")
    supp_count = sum(v for k, v in sources.items() if k.startswith("supplemental"))
    print(f"  Supplemental:       {supp_count:>8,}")
    print(f"  Confidence:")
    for bucket in sorted(confidence_buckets.keys()):
        count = confidence_buckets[bucket]
        bar = "█" * max(1, count * 40 // len(merged))
        print(f"    {bucket}: {count:>7,} {bar}")
    print(f"  Output:             {output_file}")
    print(f"  Safe output:        {safe_file}")
    print(f"  Excluded:           {exclude_file}")
    print(f"{'=' * 60}\n")

    return dataset["meta"]


def main():
    parser = argparse.ArgumentParser(description="HinglishKosh dictionary pipeline")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/output"))
    parser.add_argument("--no-supplemental", action="store_true")
    parser.add_argument("--skip-safety", action="store_true", help="Skip safety filter")
    args = parser.parse_args()

    run_pipeline(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        include_supplemental=not args.no_supplemental,
        skip_safety=args.skip_safety,
    )


if __name__ == "__main__":
    main()
