"""ML-based toxicity classifier using Hugging Face models.

Wraps the IndicBERT toxicity detector or similar models for contextual toxicity detection.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ToxicityClassifier:
    """ML-based toxicity classifier for Hindi/Hinglish text.

    Uses Hugging Face transformers pipeline for inference.
    Falls back to a simple heuristic if model is unavailable.
    """

    def __init__(self, model_name: str = "tsmaitry/indic-toxicity-detector", threshold: float = 0.70):
        """Initialize the classifier.

        Args:
            model_name: Hugging Face model identifier.
            threshold: Confidence threshold for toxicity flagging.
        """
        self.model_name = model_name
        self.threshold = threshold
        self._pipeline = None
        self._available = False

        self._try_load_model()

    def _try_load_model(self) -> None:
        """Attempt to load the Hugging Face pipeline."""
        try:
            from transformers import pipeline as hf_pipeline

            logger.info("Loading toxicity model: %s", self.model_name)
            self._pipeline = hf_pipeline(
                "text-classification",
                model=self.model_name,
                top_k=None,
            )
            self._available = True
            logger.info("Toxicity model loaded successfully")
        except Exception as e:
            logger.warning("Could not load toxicity model (%s): %s", self.model_name, e)
            self._available = False

    def classify(self, text: str) -> dict[str, Any]:
        """Classify text for toxicity.

        Returns:
            {
                "toxic": bool,
                "toxicity_score": float (0.0-1.0),
                "model_used": str,
                "labels": list of label scores
            }
        """
        if not text or not text.strip():
            return {
                "toxic": False,
                "toxicity_score": 0.0,
                "model_used": "none",
                "labels": [],
            }

        if self._available and self._pipeline:
            return self._classify_with_model(text)
        else:
            return self._classify_heuristic(text)

    def _classify_with_model(self, text: str) -> dict[str, Any]:
        """Classify using the loaded ML model."""
        try:
            results = self._pipeline(text)
            if results and isinstance(results[0], list):
                labels = results[0]
            else:
                labels = results

            # Extract toxicity score
            toxicity_score = 0.0
            for label in labels:
                if isinstance(label, dict):
                    lbl = label.get("label", "").lower()
                    score = label.get("score", 0.0)
                    if "toxic" in lbl or "hate" in lbl or "offensive" in lbl:
                        toxicity_score = max(toxicity_score, score)

            return {
                "toxic": toxicity_score >= self.threshold,
                "toxicity_score": toxicity_score,
                "model_used": self.model_name,
                "labels": labels,
            }
        except Exception as e:
            logger.error("Model classification failed: %s", e)
            return self._classify_heuristic(text)

    def _classify_heuristic(self, text: str) -> dict[str, Any]:
        """Simple heuristic fallback when ML model is unavailable.

        This is a basic approach — not recommended for production.
        """
        # Simple heuristic based on common patterns
        lower = text.lower()
        toxic_indicators = ["hate", "kill", "die", "stupid", "idiot"]
        score = 0.0
        for indicator in toxic_indicators:
            if indicator in lower:
                score += 0.3

        return {
            "toxic": min(score, 1.0) >= self.threshold,
            "toxicity_score": min(score, 1.0),
            "model_used": "heuristic",
            "labels": [{"label": "toxic", "score": min(score, 1.0)}],
        }

    @property
    def is_available(self) -> bool:
        """Check if ML model is available."""
        return self._available
