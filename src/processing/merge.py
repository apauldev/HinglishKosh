"""Merge WordNet and Wiktionary dictionaries into a unified dataset.

Priority: WordNet entries take precedence on conflicts.
"""

from __future__ import annotations

import logging
from typing import Any

from rapidfuzz import fuzz

from src.processing.dedup import _definition_hash, _normalize_hindi, _normalize_roman

logger = logging.getLogger(__name__)


def _find_matching_entry(
    target: dict[str, Any],
    candidates: list[dict[str, Any]],
    threshold: int = 85,
) -> dict[str, Any] | None:
    """Find the best matching entry in candidates using fuzzy matching.

    Returns the best match above threshold, or None.
    """
    target_hindi = _normalize_hindi(target.get("word_hindi", ""))
    target_roman = _normalize_roman(target.get("word_hinglish_roman", ""))

    best_match = None
    best_score = 0

    for candidate in candidates:
        cand_hindi = _normalize_hindi(candidate.get("word_hindi", ""))
        cand_roman = _normalize_roman(candidate.get("word_hinglish_roman", ""))

        # Hindi word similarity (exact or normalized)
        if target_hindi == cand_hindi:
            hindi_score = 100
        else:
            hindi_score = fuzz.ratio(target_hindi, cand_hindi)

        # Roman similarity
        if target_roman and cand_roman:
            roman_score = fuzz.ratio(target_roman, cand_roman)
        else:
            roman_score = 0

        # Combined score (weighted towards Hindi match)
        score = max(hindi_score, roman_score, (hindi_score * 0.7 + roman_score * 0.3))

        if score > best_score and score >= threshold:
            best_score = score
            best_match = candidate

    return best_match


def merge_dictionaries(
    wordnet_entries: list[dict[str, Any]],
    wiktionary_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge WordNet and Wiktionary dictionaries.

    Strategy:
    1. Start with all WordNet entries (higher quality)
    2. For each Wiktionary entry, check if a WordNet match exists
    3. If match found: merge synsets/examples, keep WordNet definition
    4. If no match: add Wiktionary entry as-is (extended coverage)
    """
    merged = []
    matched_wk_ids = set()
    merge_count = 0

    # Index WordNet entries by Hindi word for fast lookup
    wn_index: dict[str, list[dict[str, Any]]] = {}
    for entry in wordnet_entries:
        key = _normalize_hindi(entry.get("word_hindi", ""))
        if key not in wn_index:
            wn_index[key] = []
        wn_index[key].append(entry)

    # Step 1: Add all WordNet entries
    merged.extend(wordnet_entries)
    logger.info("Added %d WordNet entries as base", len(wordnet_entries))

    # Step 2: Try to match each Wiktionary entry
    for wk_entry in wiktionary_entries:
        wk_hindi = _normalize_hindi(wk_entry.get("word_hindi", ""))
        wk_def_hash = _definition_hash(wk_entry.get("definition", ""))

        # Try exact match first
        wn_matches = wn_index.get(wk_hindi, [])

        matched = False
        for wn_entry in wn_matches:
            wn_def_hash = _definition_hash(wn_entry.get("definition", ""))
            if wn_def_hash == wk_def_hash:
                # Same definition — merge synsets and examples
                wn_synsets = wn_entry.get("synsets", [])
                for s in wk_entry.get("synsets", []):
                    if s not in wn_synsets:
                        wn_synsets.append(s)
                wn_entry["synsets"] = wn_synsets

                # Merge examples
                wk_examples = wk_entry.get("all_examples", [])
                if wk_examples:
                    wn_examples = wn_entry.get("all_examples", [])
                    for ex in wk_examples:
                        if ex and ex not in wn_examples:
                            wn_examples.append(ex)
                    wn_entry["all_examples"] = wn_examples
                    if not wn_entry.get("example_sentence") and wk_examples:
                        wn_entry["example_sentence"] = wk_examples[0]

                matched_wk_ids.add(wk_entry["id"])
                merge_count += 1
                matched = True
                break

        if not matched:
            # No WordNet match — add as extended coverage
            merged.append(wk_entry)

    logger.info(
        "Merge complete: %d total entries (%d WordNet + %d Wiktionary, %d merged)",
        len(merged), len(wordnet_entries), len(wiktionary_entries), merge_count,
    )
    return merged


def assign_ids(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Assign unified sequential IDs in HIN-XXXXX format."""
    for i, entry in enumerate(entries, 1):
        entry["id"] = f"HIN-{i:05d}"
    return entries
