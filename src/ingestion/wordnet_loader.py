"""Loader for Hindi WordNet data from IIT Bombay (IndoWordNet).

Data format: tab-separated text files where each line is:
    synset_id<TAB>word1,word2,...<TAB>gloss:example1  /  example2<TAB>pos

Download source: Dropbox link via pyiwn or direct download.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _parse_gloss_examples(raw: str) -> tuple[str, list[str]]:
    """Parse 'gloss:"example1  /  example2' into (gloss, [examples])."""
    raw = raw.strip()
    if not raw:
        return "", []

    if ':"' in raw:
        gloss, examples_block = raw.split(':"', 1)
        examples = [e.strip().strip('"') for e in examples_block.split("  /  ") if e.strip()]
    else:
        gloss = raw
        examples = []

    return gloss.strip(), examples


def _make_roman(word: str) -> str:
    """Best-effort romanization stub — returns lowercased word as-is.

    Full transliteration is handled by the transliterate module later.
    """
    return word.lower()


def parse_synset_file(filepath: Path) -> list[dict[str, Any]]:
    """Parse a single WordNet synset file (e.g. all.hindi).

    Returns a list of dicts with keys:
        synset_id, words, gloss, examples, pos
    """
    entries = []
    with open(filepath, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 4:
                logger.warning("Skipping malformed line %d in %s: %s", lineno, filepath.name, line[:80])
                continue

            synset_id_str, words_str, gloss_examples_str, pos = parts[0], parts[1], parts[2], parts[3]

            try:
                synset_id = int(synset_id_str)
            except ValueError:
                logger.warning("Invalid synset ID at line %d: %s", lineno, synset_id_str)
                continue

            words = [w.strip() for w in words_str.split(",") if w.strip()]
            gloss, examples = _parse_gloss_examples(gloss_examples_str)

            entries.append({
                "synset_id": synset_id,
                "words": words,
                "gloss": gloss,
                "examples": examples,
                "pos": pos.strip(),
            })

    return entries


def load_wordnet(data_dir: Path) -> list[dict[str, Any]]:
    """Load all WordNet synset data from the data directory.

    Expects structure:
        data_dir/
            synsets/
                all.hindi
            synset_relations/  (optional, for future use)

    Returns a list of normalized dictionary entries.
    """
    # Check common extraction layouts
    synsets_dir = data_dir / "synsets"
    if not synsets_dir.exists():
        # Handle iwn_data.tar.gz extraction: data_dir/iwn_data/synsets/
        iwn_synsets = data_dir / "iwn_data" / "synsets"
        if iwn_synsets.exists():
            synsets_dir = iwn_synsets
        else:
            raise FileNotFoundError(f"Synsets directory not found: {synsets_dir}")

    # Load all language synset files (focus on Hindi)
    hindi_file = synsets_dir / "all.hindi"
    if not hindi_file.exists():
        # Fallback: try any available file
        files = list(synsets_dir.glob("all.*"))
        if not files:
            raise FileNotFoundError(f"No synset files found in {synsets_dir}")
        hindi_file = files[0]
        logger.info("Using %s as Hindi synset source", hindi_file.name)

    raw_entries = parse_synset_file(hindi_file)
    logger.info("Parsed %d raw synsets from %s", len(raw_entries), hindi_file.name)

    # Normalize into unified schema
    normalized = []
    for entry in raw_entries:
        head_word = entry["words"][0] if entry["words"] else ""
        for word in entry["words"]:
            entry_id = f"WN-{entry['synset_id']}"
            normalized.append({
                "id": entry_id,
                "word_hindi": word,
                "word_hinglish_roman": _make_roman(word),
                "definition": entry["gloss"],
                "part_of_speech": entry["pos"],
                "example_sentence": entry["examples"][0] if entry["examples"] else "",
                "all_examples": entry["examples"],
                "synsets": [f"iwn-{entry['synset_id']}"],
                "head_word": head_word,
                "source": "WordNet",
                "confidence_score": 1.0,
                "toxicity_flags": [],
                "severity_score": 0.0,
            })

    return normalized


def load_english_hindi_linkage(filepath: Path) -> dict[int, str]:
    """Load English-Hindi synset linkage TSV from IWN-En.

    TSV format: english_offset<TAB>hindi_synset_id<TAB>english_word<TAB>hindi_word

    Returns a dict mapping hindi_synset_id -> english_word.
    """
    linkage = {}
    if not filepath.exists():
        logger.warning("Linkage file not found: %s", filepath)
        return linkage

    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                try:
                    hindi_synset_id = int(parts[1])
                    english_word = parts[2]
                    linkage[hindi_synset_id] = english_word
                except (ValueError, IndexError):
                    continue

    logger.info("Loaded %d English-Hindi linkage pairs", len(linkage))
    return linkage
