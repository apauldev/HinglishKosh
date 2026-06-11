"""Severity scoring for Hindi profanity entries — dictionary-only mode.

This module uses the pre-built profanity wordlist to flag entries.
No ML inference — fast and deterministic.
"""

from __future__ import annotations

from typing import Any

from src.safety.profanity_list import ProfanityMatcher


def score_severity(
    word: str,
    pos: str = "",
    gloss: str = "",
    gloss_hi: str = "",
    examples: str = "",
    **_kwargs: object,
) -> dict[str, object]:
    """Check if a word contains profanity using dictionary lookup.

    Args:
        word: The Hindi word (romanized).
        pos: Part of speech (unused in dict-only mode).
        gloss: English gloss (used for profanity check).
        gloss_hi: Hindi gloss in Devanagari (unused in dict-only mode).
        examples: Example sentences (used for profanity check).
        **_kwargs: Additional fields (ignored).

    Returns:
        dict with:
            - profanity: bool — True if word or examples contain profanity
            - severity_score: float — 0.0 (clean) or 1.0 (profane), kept for schema compat
    """
    # Combine all text fields that might contain profanity
    text_to_check = " ".join(filter(None, [word, gloss, examples]))

    matcher = ProfanityMatcher()
    is_profane = matcher.contains_profanity(text_to_check)

    return {
        "profanity": is_profane,
        "severity_score": 1.0 if is_profane else 0.0,
    }


def flag_entries(
    entries: list[dict[str, Any]],
    profanity_matcher: ProfanityMatcher,
    _toxicity_classifier: Any = None,
) -> list[dict[str, Any]]:
    """Flag all entries with profanity using dictionary-only lookup.

    Args:
        entries: List of dictionary entries.
        profanity_matcher: ProfanityMatcher instance.
        _toxicity_classifier: Ignored (ML not used in dict-only mode).

    Returns:
        Same list with `profanity` and `severity_score` fields added.
    """
    for entry in entries:
        word = entry.get("word_hinglish_roman", "")
        # Only check the word itself, not definitions/examples
        # This avoids false positives like "land" in "land of the Aryans"
        is_profane = profanity_matcher.contains_profanity(word)
        entry["profanity"] = is_profane
        entry["severity_score"] = 1.0 if is_profane else 0.0

    return entries
