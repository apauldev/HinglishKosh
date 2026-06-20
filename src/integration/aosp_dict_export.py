"""AOSP .dict file export for OpenBoard/HeliBoard/FUTO keyboard integration.

Generates dictionary files compatible with Android's UserDictionary format,
which is supported by OpenBoard, HeliBoard, and FUTO Keyboard.

The AOSP UserDictionary frequency range is 1-255. This module maps the
dictionary's confidence scores (0.30-1.00) into that range so keyboards
correctly prioritize suggestions.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Android UserDictionary frequency range
_MIN_FREQ = 1
_MAX_FREQ = 255

# Confidence range from the pipeline scoring system
_MIN_CONF = 0.30
_MAX_CONF = 1.00


def confidence_to_frequency(confidence: float) -> int:
    """Map a confidence score (0.30-1.00) to Android frequency (1-255).

    Values below MIN_CONF are floored to MIN_FREQ (covers toxic entries
    that were pinned to 0.30). Values at or above MAX_CONF map to MAX_FREQ.
    The mapping is linear between these endpoints.
    """
    if confidence >= _MAX_CONF:
        return _MAX_FREQ
    if confidence <= _MIN_CONF:
        return _MIN_FREQ
    ratio = (confidence - _MIN_CONF) / (_MAX_CONF - _MIN_CONF)
    return int(_MIN_FREQ + ratio * (_MAX_FREQ - _MIN_FREQ))


def export_aosp_dict(
    entries: list[dict[str, Any]],
    output_path: Path,
    locale: str = "hi",
    dedup: bool = True,
) -> int:
    """Export dictionary entries to AOSP .dict format.

    Format: Tab-separated values with columns:
        word<TAB>frequency<TAB>locale<TAB>shortcut<TAB>bigram<TAB>pos

    Args:
        entries: Dictionary entries to export.
        output_path: Path to write the .dict file.
        locale: Language locale code.
        dedup: If True, collapse duplicate roman words keeping highest frequency.

    Returns:
        Number of entries exported.
    """
    rows: list[list[str]] = []
    seen: dict[str, int] = {} if dedup else None

    for entry in entries:
        word = entry.get("word_hinglish_roman", "")
        if not word:
            continue

        if entry.get("severity_score", 0) >= 0.5:
            continue

        freq = confidence_to_frequency(entry.get("confidence_score", _MIN_CONF))
        pos = entry.get("part_of_speech", "")

        if dedup:
            idx = seen.get(word)
            if idx is not None:
                existing_freq = int(rows[idx][1])
                if freq <= existing_freq:
                    continue
                rows[idx][1] = str(freq)
            else:
                seen[word] = len(rows)
                rows.append([word, str(freq), locale, "", "", pos])
        else:
            rows.append([word, str(freq), locale, "", "", pos])

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerows(rows)

    logger.info("Exported %d entries to %s", len(rows), output_path)
    return len(rows)


def export_words_txt(
    entries: list[dict[str, Any]],
    output_path: Path,
) -> int:
    """Export a simple word list (one word per line) for quick integration.

    Returns number of entries exported.
    """
    words = set()
    for entry in entries:
        roman = entry.get("word_hinglish_roman", "")
        if roman and entry.get("severity_score", 0) < 0.5:
            words.add(roman.lower())

    with open(output_path, "w", encoding="utf-8") as f:
        for word in sorted(words):
            f.write(word + "\n")

    logger.info("Exported %d unique words to %s", len(words), output_path)
    return len(words)
