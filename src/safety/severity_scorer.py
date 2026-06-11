"""Severity scoring — multi-model consensus for toxicity detection.

Combines dictionary-based and ML-based results into a unified severity score.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def compute_severity(
    wordlist_matches: list[dict[str, Any]],
    ml_result: dict[str, Any],
    weights: tuple[float, float] = (0.4, 0.6),
) -> dict[str, Any]:
    """Compute combined severity score from dictionary and ML results.

    Args:
        wordlist_matches: Results from ProfanityMatcher.check_text().
        ml_result: Result from ToxicityClassifier.classify().
        weights: (dictionary_weight, ml_weight). Must sum to 1.0.

    Returns:
        {
            "severity_score": float (0.0-1.0),
            "toxicity_flags": list of flag strings,
            "is_toxic": bool,
            "components": dict of individual scores
        }
    """
    dict_weight, ml_weight = weights

    # Dictionary-based severity
    dict_severity = 0.0
    dict_flags = []
    for match in wordlist_matches:
        sev = match.get("severity", 0.0)
        cat = match.get("category", "profanity")
        dict_severity = max(dict_severity, sev)
        if cat not in dict_flags:
            dict_flags.append(cat)

    # ML-based severity
    ml_severity = ml_result.get("toxicity_score", 0.0)
    ml_toxic = ml_result.get("toxic", False)

    # Combined severity
    combined_score = (dict_severity * dict_weight) + (ml_severity * ml_weight)

    # Build flags
    toxicity_flags = list(set(dict_flags))
    if ml_toxic and "contextual_toxicity" not in toxicity_flags:
        toxicity_flags.append("contextual_toxicity")

    # Determine overall toxicity
    is_toxic = combined_score >= 0.5 or (dict_severity >= 0.8) or ml_toxic

    return {
        "severity_score": round(combined_score, 4),
        "toxicity_flags": toxicity_flags,
        "is_toxic": is_toxic,
        "components": {
            "dictionary_severity": dict_severity,
            "ml_severity": ml_severity,
            "dictionary_flags": dict_flags,
            "ml_labels": ml_result.get("labels", []),
        },
    }


def flag_entries(
    entries: list[dict[str, Any]],
    profanity_matcher: Any,
    toxicity_classifier: Any,
    threshold: float = 0.70,
) -> list[dict[str, Any]]:
    """Process dictionary entries through the safety filter.

    Adds toxicity_flags and severity_score to each entry.
    """
    flagged = []

    for entry in entries:
        word = entry.get("word_hindi", "")
        definition = entry.get("definition", "")
        example = entry.get("example_sentence", "")

        # Combine text for checking
        check_text = f"{word} {definition} {example}".strip()

        # Dictionary check
        dict_matches = profanity_matcher.check_text(check_text)

        # ML check
        ml_result = toxicity_classifier.classify(check_text)

        # Compute severity
        severity = compute_severity(dict_matches, ml_result)

        # Update entry
        entry["toxicity_flags"] = severity["toxicity_flags"]
        entry["severity_score"] = severity["severity_score"]

        flagged.append(entry)

    return flagged
