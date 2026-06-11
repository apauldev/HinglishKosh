"""AOSP .dict file export for OpenBoard/HeliBoard keyboard integration.

Generates dictionary files compatible with Android's UserDictionary format.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def export_aosp_dict(
    entries: list[dict[str, Any]],
    output_path: Path,
    locale: str = "hi",
) -> int:
    """Export dictionary entries to AOSP .dict format.

    Format: Tab-separated values with columns:
        word<TAB>frequency<TAB>locale<TAB>shortcut<TAB>bigram<TAB>pos

    Args:
        entries: Dictionary entries to export.
        output_path: Path to write the .dict file.
        locale: Language locale code.

    Returns:
        Number of entries exported.
    """
    count = 0
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")

        for entry in entries:
            word = entry.get("word_hinglish_roman", "")
            if not word:
                continue

            # Skip toxic entries
            if entry.get("severity_score", 0) >= 0.5:
                continue

            # AOSP UserDictionary columns
            # word, freq, locale, shortcut, bigram, pos
            writer.writerow(
                [
                    word,
                    int(entry.get("confidence_score", 0.5) * 1000),  # frequency score
                    locale,
                    "",  # shortcut (optional)
                    "",  # bigram (optional)
                    entry.get("part_of_speech", ""),
                ]
            )
            count += 1

    logger.info("Exported %d entries to %s", count, output_path)
    return count


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
