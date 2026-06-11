"""Loader for supplemental Hinglish datasets (CoMuMDR, eval_hinglish_top_v2, etc.)."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _load_csv_dataset(filepath: Path) -> list[dict[str, Any]]:
    """Load a CSV dataset with flexible column detection."""
    entries = []
    with open(filepath, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return entries

        # Normalize column names
        cols = {c.lower().strip(): c for c in reader.fieldnames}

        for row in reader:
            # Try to find Hindi word column
            hindi_col = (cols.get("hindi") or cols.get("word_hindi")
                         or cols.get("hindi_word") or cols.get("word"))
            eng_col = (cols.get("english") or cols.get("definition")
                       or cols.get("meaning") or cols.get("eng"))
            roman_col = (cols.get("roman") or cols.get("hinglish")
                         or cols.get("romanized") or cols.get("transliteration"))
            pos_col = cols.get("pos") or cols.get("part_of_speech") or cols.get("type")

            word_hindi = (row.get(hindi_col) or "").strip() if hindi_col else ""
            definition = (row.get(eng_col) or "").strip() if eng_col else ""
            roman = (row.get(roman_col) or "").strip() if roman_col else ""
            pos = (row.get(pos_col) or "").strip() if pos_col else ""

            if not word_hindi and not definition:
                continue

            entries.append({
                "word_hindi": word_hindi,
                "word_hinglish_roman": roman,
                "definition": definition,
                "part_of_speech": pos,
                "source": "supplemental",
                "confidence_score": 0.7,
            })

    return entries


def _load_json_dataset(filepath: Path) -> list[dict[str, Any]]:
    """Load a JSON dataset (list of objects or JSONL)."""
    content = filepath.read_text(encoding="utf-8")
    content_stripped = content.strip()

    # Try JSONL first (one object per line)
    if "\n" in content_stripped:
        try:
            first_line = content_stripped.split("\n", 1)[0]
            json.loads(first_line)
            # It's JSONL
            entries = []
            for lineno, line in enumerate(content_stripped.split("\n"), 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    entries.append(data)
                except json.JSONDecodeError:
                    continue
            return entries
        except json.JSONDecodeError:
            pass

    # Try as JSON array
    try:
        data = json.loads(content_stripped)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass

    return []


def load_supplemental(data_dir: Path) -> list[dict[str, Any]]:
    """Load all supplemental datasets from the directory.

    Supports: CSV, JSON, JSONL files.
    """
    all_entries = []
    files = list(data_dir.glob("*.*"))

    if not files:
        logger.info("No supplemental files found in %s", data_dir)
        return all_entries

    for filepath in files:
        if filepath.suffix.lower() == ".csv":
            entries = _load_csv_dataset(filepath)
        elif filepath.suffix.lower() in (".json", ".jsonl"):
            entries = _load_json_dataset(filepath)
        else:
            logger.info("Skipping unsupported file: %s", filepath.name)
            continue

        # Normalize entries into unified schema
        for entry in entries:
            word = (entry.get("word_hindi") or entry.get("hindi")
                    or entry.get("word") or "")
            definition = (entry.get("definition") or entry.get("meaning")
                          or entry.get("english") or "")
            roman = (entry.get("word_hinglish_roman") or entry.get("roman")
                     or entry.get("hinglish") or "")
            pos = entry.get("part_of_speech") or entry.get("pos") or entry.get("type") or ""

            if not word and not definition:
                continue

            all_entries.append({
                "id": f"SUP-{filepath.stem}-{len(all_entries)}",
                "word_hindi": word,
                "word_hinglish_roman": roman,
                "definition": definition,
                "part_of_speech": pos,
                "example_sentence": "",
                "all_examples": [],
                "synsets": [],
                "source": f"supplemental/{filepath.stem}",
                "confidence_score": 0.7,
                "toxicity_flags": [],
                "severity_score": 0.0,
            })

        logger.info("Loaded %d entries from %s", len(entries), filepath.name)

    logger.info("Total supplemental entries: %d", len(all_entries))
    return all_entries
