"""Loader for Wiktionary data from kaikki.org (JSONL format).

Data format: one JSON object per line with fields:
    word, lang, lang_code, pos, senses[], forms[], sounds[], etc.

Download: https://kaikki.org/dictionary/Hindi/kaikki.org-dictionary-Hindi.jsonl
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _extract_roman(forms: list[dict]) -> str:
    """Extract romanization from forms array."""
    for form in forms:
        tags = form.get("tags", [])
        if "romanization" in tags or "roman" in tags:
            return form.get("form", "")
    # Fallback: try Latin script form
    for form in forms:
        f = form.get("form", "")
        if f and all(ord(c) < 0x980 or 0x980 <= ord(c) <= 0x9FF or ord(c) > 0x10FF for c in f):
            if f.isascii():
                return f
    return ""


def _extract_definition(sense: dict) -> str:
    """Extract the best definition text from a sense object."""
    glosses = sense.get("glosses", [])
    if glosses:
        return glosses[0]
    raw_glosses = sense.get("raw_glosses", [])
    if raw_glosses:
        # Strip parenthetical qualifiers
        text = raw_glosses[0]
        text = __import__("re").sub(r"\([^)]*\)\s*", "", text).strip()
        return text
    return ""


def _extract_example(sense: dict) -> str:
    """Extract the first example sentence from a sense object."""
    examples = sense.get("examples", [])
    for ex in examples:
        if isinstance(ex, dict):
            text = ex.get("text", "")
            if text:
                # Append English translation if available
                translation = ex.get("translation", "")
                if translation:
                    return f"{text} ({translation})"
                return text
        elif isinstance(ex, str):
            return ex
    return ""


def _extract_tags(sense: dict) -> list[str]:
    """Extract qualifier tags from a sense."""
    return sense.get("tags", [])


def parse_wiktionary_jsonl(filepath: Path, lang_code: str = "hi") -> list[dict[str, Any]]:
    """Parse the kaikki.org JSONL file for a specific language.

    Args:
        filepath: Path to the JSONL file.
        lang_code: ISO 639 code to filter (default: "hi" for Hindi).

    Returns:
        List of raw parsed entries.
    """
    entries = []
    skipped = 0
    malformed = 0

    with open(filepath, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                if malformed <= 5:
                    logger.warning("Malformed JSON at line %d: %s", lineno, line[:100])
                continue

            # Skip redirects
            if "redirect" in data:
                continue

            # Filter by language
            if data.get("lang_code") != lang_code:
                skipped += 1
                continue

            entries.append(data)

    logger.info(
        "Parsed %d entries for lang=%s (skipped %d other langs, %d malformed)",
        len(entries),
        lang_code,
        skipped,
        malformed,
    )
    return entries


def load_wiktionary(data_dir: Path, lang_code: str = "hi") -> list[dict[str, Any]]:
    """Load and normalize Wiktionary data into unified schema.

    Expects:
        data_dir/kaikki-hindi.jsonl  (or similar)

    Returns:
        List of normalized dictionary entries.
    """
    # Find the JSONL file
    jsonl_files = list(data_dir.glob("*.jsonl"))
    if not jsonl_files:
        raise FileNotFoundError(f"No JSONL files found in {data_dir}")

    filepath = jsonl_files[0]
    logger.info("Loading Wiktionary data from %s", filepath.name)

    raw_entries = parse_wiktionary_jsonl(filepath, lang_code)

    # Normalize into unified schema
    normalized = []
    for entry in raw_entries:
        word = entry.get("word", "")
        pos = entry.get("pos", "")
        forms = entry.get("forms", [])
        roman = _extract_roman(forms)

        senses = entry.get("senses", [])
        if not senses:
            # Entry has no definitions, skip
            continue

        for i, sense in enumerate(senses):
            definition = _extract_definition(sense)
            if not definition:
                continue

            example = _extract_example(sense)
            tags = _extract_tags(sense)

            # Build sense-specific ID
            entry_id = f"WK-{word}-{pos}-{i}" if senses else f"WK-{word}-{pos}"

            # Collect synonyms, antonyms from sense
            synonyms = [s.get("word", "") for s in sense.get("synonyms", []) if s.get("word")]
            antonyms = [s.get("word", "") for s in sense.get("antonyms", []) if s.get("word")]

            normalized.append(
                {
                    "id": entry_id,
                    "word_hindi": word,
                    "word_hinglish_roman": roman,
                    "definition": definition,
                    "part_of_speech": pos,
                    "example_sentence": example,
                    "all_examples": [example] if example else [],
                    "synsets": [],
                    "tags": tags,
                    "synonyms": synonyms,
                    "antonyms": antonyms,
                    "source": "Wiktionary",
                    "confidence_score": 0.85,
                    "toxicity_flags": [],
                    "severity_score": 0.0,
                }
            )

    logger.info("Normalized %d sense-level entries from Wiktionary", len(normalized))
    return normalized
