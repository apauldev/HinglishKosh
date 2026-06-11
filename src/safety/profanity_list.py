"""Profanity wordlist management — dictionary-based offensive content detection.

Compiles a master profanity list from multiple sources with severity levels.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Built-in common Hindi/Hinglish profanity (abbreviated for licensing reasons)
# In production, load from bekindprofanityfilter or curated wordlist files.
_BUILTIN_PROFANITY: dict[str, dict[str, Any]] = {
    # Format: "word": {"severity": 0.0-1.0, "category": "profanity|hate_speech|slur"}
    # This is a placeholder — real data should be loaded from external files.
}


class ProfanityMatcher:
    """Dictionary-based profanity detection with character variation support."""

    def __init__(self, wordlist_path: Path | None = None, threshold: float = 0.70):
        """Initialize with an optional external wordlist file.

        Args:
            wordlist_path: Path to JSON wordlist file.
            threshold: Minimum severity score to flag (0.0-1.0).
        """
        self.threshold = threshold
        self.wordlist: dict[str, dict[str, Any]] = dict(_BUILTIN_PROFANITY)
        self._char_map = self._build_char_map()

        if wordlist_path and wordlist_path.exists():
            self.load_wordlist(wordlist_path)

    def _build_char_map(self) -> dict[str, str]:
        """Build leet-speak / character substitution map."""
        return {
            "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
            "7": "t", "8": "b", "9": "g", "@": "a", "$": "s",
            "!": "i", "+": "t", "ph": "f", "kk": "k",
            # Devanagari-Roman common substitutions
            "aa": "a", "ee": "e", "oo": "o", "ii": "i", "uu": "u",
        }

    def load_wordlist(self, filepath: Path) -> int:
        """Load profanity wordlist from JSON file.

        Expected format:
        {
            "word": {"severity": 0.9, "category": "profanity"},
            ...
        }

        Returns number of entries loaded.
        """
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
            count = 0
            for word, meta in data.items():
                self.wordlist[word.lower()] = meta
                count += 1
            logger.info("Loaded %d profanity entries from %s", count, filepath.name)
            return count
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load wordlist from %s: %s", filepath, e)
            return 0

    def _normalize(self, text: str) -> str:
        """Normalize text for matching."""
        text = text.lower().strip()
        # Apply character substitutions
        for old, new in self._char_map.items():
            text = text.replace(old, new)
        # Remove non-alphanumeric
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def check_word(self, word: str) -> dict[str, Any] | None:
        """Check a single word against the profanity list.

        Returns match info dict or None if clean.
        """
        normalized = self._normalize(word)

        # Direct match
        if normalized in self.wordlist:
            entry = self.wordlist[normalized]
            return {
                "matched": True,
                "input": word,
                "normalized": normalized,
                "severity": entry.get("severity", 0.5),
                "category": entry.get("category", "profanity"),
                "match_type": "direct",
            }

        # Check if word contains a profanity substring
        for profanity, meta in self.wordlist.items():
            if len(profanity) >= 3 and profanity in normalized:
                return {
                    "matched": True,
                    "input": word,
                    "normalized": normalized,
                    "matched_word": profanity,
                    "severity": meta.get("severity", 0.5),
                    "category": meta.get("category", "profanity"),
                    "match_type": "substring",
                }

        return None

    def check_text(self, text: str) -> list[dict[str, Any]]:
        """Check a full text for profanity matches.

        Returns list of all matches found.
        """
        words = text.split()
        matches = []
        for word in words:
            result = self.check_word(word)
            if result:
                matches.append(result)
        return matches

    def is_clean(self, text: str) -> bool:
        """Check if text is clean (no profanity above threshold)."""
        matches = self.check_text(text)
        return not any(m["severity"] >= self.threshold for m in matches)
