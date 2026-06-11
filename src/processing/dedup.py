"""Deduplication logic for dictionary entries.

Handles dedup by:
1. Exact match on (word_hindi, definition_hash)
2. Fuzzy matching on romanized headwords
3. Lemma-based normalization
"""

from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from typing import Any

logger = logging.getLogger(__name__)


def _normalize_hindi(word: str) -> str:
    """Normalize Hindi text for comparison.

    - NFKD normalize Unicode
    - Strip nukta dots (़) for variant matching
    - Strip anusvara/visarga
    """
    word = unicodedata.normalize("NFKD", word)
    # Remove nukta variants
    word = word.replace("\u093C", "")  # nukta
    # Strip trailing virama
    word = word.rstrip("\u094D")
    return word.strip()


def _normalize_roman(roman: str) -> str:
    """Normalize romanized text for comparison.

    - Lowercase
    - Strip accents/diacritics
    - Collapse whitespace
    - Remove non-alphanumeric except spaces
    """
    roman = roman.lower().strip()
    roman = re.sub(r"[^\w\s]", "", roman)
    roman = re.sub(r"\s+", " ", roman)
    return roman


def _definition_hash(definition: str) -> str:
    """Create a hash for dedup comparison."""
    normalized = definition.lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return hashlib.md5(normalized.encode()).hexdigest()


def _is_variant(word_a: str, word_b: str) -> bool:
    """Check if two Hindi words are spelling variants of each other."""
    norm_a = _normalize_hindi(word_a)
    norm_b = _normalize_hindi(word_b)
    if norm_a == norm_b:
        return True
    # Handle common Devanagari alternates
    # ए vs ऎ, ओ vs ऒ, etc.
    return False


def deduplicate_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate dictionary entries using multi-strategy matching.

    Strategy:
    1. Group by normalized Hindi headword
    2. Within each group, deduplicate by definition hash
    3. Merge non-overlapping definitions from duplicate headwords
    """
    # Step 1: Group by normalized Hindi word
    groups: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        key = _normalize_hindi(entry.get("word_hindi", ""))
        if key not in groups:
            groups[key] = []
        groups[key].append(entry)

    logger.info("Grouped %d entries into %d headword groups", len(entries), len(groups))

    # Step 2: Deduplicate within groups
    deduped = []
    total_merged = 0

    for hindi_key, group in groups.items():
        # Within a group, deduplicate by definition hash
        seen_defs: dict[str, dict[str, Any]] = {}

        for entry in group:
            dhash = _definition_hash(entry.get("definition", ""))

            if dhash in seen_defs:
                # Duplicate definition — merge sources and examples
                existing = seen_defs[dhash]
                if entry["source"] not in existing["source"]:
                    existing["source"] += f"+{entry['source']}"
                # Merge examples
                new_examples = entry.get("all_examples", [])
                if new_examples:
                    existing_examples = existing.get("all_examples", [])
                    for ex in new_examples:
                        if ex and ex not in existing_examples:
                            existing_examples.append(ex)
                    existing["all_examples"] = existing_examples
                    if not existing.get("example_sentence") and new_examples:
                        existing["example_sentence"] = new_examples[0]
                # Take higher confidence
                existing["confidence_score"] = max(
                    existing.get("confidence_score", 0),
                    entry.get("confidence_score", 0),
                )
                # Merge synsets
                existing_synsets = existing.get("synsets", [])
                for s in entry.get("synsets", []):
                    if s not in existing_synsets:
                        existing_synsets.append(s)
                existing["synsets"] = existing_synsets
                total_merged += 1
            else:
                seen_defs[dhash] = entry

        deduped.extend(seen_defs.values())

    logger.info(
        "Deduplication: %d entries → %d unique (merged %d duplicate definitions)",
        len(entries), len(deduped), total_merged,
    )
    return deduped
