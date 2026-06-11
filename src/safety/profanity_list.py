"""Profanity wordlist loader and fast lookup for the safety filter."""

from __future__ import annotations

import json
import re
from pathlib import Path

# Path to the curated profanity wordlist
_PROFANITY_LIST_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "raw" / "profanity"
) / "master_list.json"


def _normalize_word(word: str) -> str:
    """Normalize a word for matching: lowercase, strip accents, collapse whitespace."""
    w = word.strip().lower()
    # Remove accent characters (common in transliterated Hindi)
    replacements = {
        "ā": "a",
        "ī": "i",
        "ū": "u",
        "ē": "e",
        "ō": "o",
        "ṛ": "r",
        "ṇ": "n",
        "ṣ": "s",
        "ḥ": "h",
        "ṁ": "m",
    }
    for old, new in replacements.items():
        w = w.replace(old, new)
    # Remove anything that's not alphanumeric or space
    w = re.sub(r"[^a-z0-9\s]", "", w)
    return w.strip()


def load_profanity_list(custom_path: str | Path | None = None) -> set[str]:
    """Load profanity words from the master list JSON file.

    Returns a set of normalized lowercase words for fast O(1) lookup.
    """
    path = Path(custom_path) if custom_path else _PROFANITY_LIST_PATH

    if not path.exists():
        # Fallback: return empty set rather than crash
        return set()

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    raw_words: list[str] = data.get("words", [])
    normalized = {_normalize_word(w) for w in raw_words if w.strip()}
    # Remove empty strings
    normalized.discard("")
    return normalized


# Module-level cached instance (loaded once at import time)
_PROFANITY_SET: set[str] = set()


def get_profanity_set() -> set[str]:
    """Return the cached profanity word set, loading it on first call."""
    global _PROFANITY_SET
    if not _PROFANITY_SET:
        _PROFANITY_SET = load_profanity_list()
    return _PROFANITY_SET


def _normalize_text(text: str) -> str:
    """Normalize text for matching: lowercase, strip accents, keep alphanumeric + spaces."""
    t = text.strip().lower()
    replacements = {
        "ā": "a",
        "ī": "i",
        "ū": "u",
        "ē": "e",
        "ō": "o",
        "ṛ": "r",
        "ṇ": "n",
        "ṣ": "s",
        "ḥ": "h",
        "ṁ": "m",
    }
    for old, new in replacements.items():
        t = t.replace(old, new)
    t = re.sub(r"[^a-z0-9\s]", "", t)
    return t


def check_profanity(text: str, custom_list: str | Path | None = None) -> bool:
    """Check if text contains any profanity words.

    Args:
        text: The text to check (Hindi or English).
        custom_list: Optional path to a custom profanity list file.

    Returns:
        True if any profanity word is found in the text, False otherwise.
    """
    if not text or not text.strip():
        return False

    profanity_set = get_profanity_set() if not custom_list else load_profanity_list(custom_list)

    if not profanity_set:
        return False

    normalized = _normalize_text(text)

    # Check each word in the text against the profanity set
    for word in normalized.split():
        if word in profanity_set:
            return True

    return False


class ProfanityMatcher:
    """Simple profanity matcher using dictionary lookup."""

    def __init__(self, custom_list: str | Path | None = None) -> None:
        self.wordlist = load_profanity_list(custom_list)

    def contains_profanity(self, text: str) -> bool:
        """Check if text contains any profanity words."""
        if not self.wordlist:
            return False
        if not text or not text.strip():
            return False
        normalized = _normalize_text(text)
        for word in normalized.split():
            if word in self.wordlist:
                return True
        return False
