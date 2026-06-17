"""FastAPI REST API for HinglishKosh dictionary lookups.

Endpoints:
    GET /lookup?word={word}&safe=true&min_confidence=0.5
    GET /search?q={query}&limit=20&safe=true&min_confidence=0.5
    GET /stats
    GET /health
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Lazy-loaded dictionary data
_dictionary: list[dict[str, Any]] = []
_safe_dictionary: list[dict[str, Any]] = []
_metadata: dict[str, Any] = {}
_index: dict[str, dict[str, Any]] = {}


def _build_index(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build hash index for O(1) exact lookup by hindi or roman."""
    idx: dict[str, dict[str, Any]] = {}
    for entry in entries:
        hindi = entry.get("word_hindi", "").lower()
        roman = entry.get("word_hinglish_roman", "").lower()
        if hindi:
            idx[hindi] = entry
        if roman and roman != hindi:
            idx[roman] = entry
    return idx


def _load_dictionary(data_dir: Path = Path("data/output")) -> None:
    """Load dictionary data from JSON files."""
    global _dictionary, _safe_dictionary, _metadata, _index

    # Load full dataset
    json_file = data_dir / "hinglish_dictionary_v1.json"
    if json_file.exists():
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
        _metadata = data.get("meta", {})
        _dictionary = data.get("dictionary", [])
        _index = _build_index(_dictionary)
        logger.info(
            "Loaded %d entries from %s (index: %d keys)",
            len(_dictionary),
            json_file,
            len(_index),
        )

    # Load safe dataset
    safe_file = data_dir / "hinglish_dictionary_v1_safe.json"
    if safe_file.exists():
        with open(safe_file, encoding="utf-8") as f:
            safe_data = json.load(f)
        _safe_dictionary = safe_data.get("dictionary", [])
        logger.info("Loaded %d safe entries from %s", len(_safe_dictionary), safe_file)


def _fuzzy_search(
    query: str,
    limit: int = 20,
    dictionary: list[dict[str, Any]] | None = None,
    use_index: bool = True,
    min_confidence: float = 0.0,
) -> list[dict[str, Any]]:
    """Fuzzy search across headwords and definitions, with confidence tiebreaking.

    Uses hash index for O(1) exact lookup, then linear scan for partial matches.
    Within each score tier, higher confidence_score entries rank first.
    """
    if dictionary is None:
        dictionary = _dictionary

    query_lower = query.lower().strip()
    if not query_lower:
        return []

    results: list[tuple[int, float, dict[str, Any]]] = []

    # O(1) exact lookup via hash index
    index = _index if _index else _build_index(dictionary)
    if use_index and query_lower in index:
        entry = index[query_lower]
        conf = entry.get("confidence_score", 0.0)
        if conf >= min_confidence:
            results.append((100, conf, entry))

    # Linear scan for partial matches and exact fallback (for safe dict without index)
    for entry in dictionary:
        score = 0
        word_hindi = entry.get("word_hindi", "").lower()
        word_roman = entry.get("word_hinglish_roman", "").lower()
        conf = entry.get("confidence_score", 0.0)

        if conf < min_confidence:
            continue

        # Exact headword match (already handled by index, but needed for safe dict)
        if word_hindi == query_lower or word_roman == query_lower:
            if not use_index:
                score = 100 if word_hindi == query_lower else 95
        elif query_lower in word_hindi:
            score = 80
        elif query_lower in word_roman:
            score = 75
        elif query_lower in entry.get("definition", "").lower():
            score = 50

        if score > 0:
            results.append((score, conf, entry))

    # Sort by score (desc), then by confidence (desc) within same tier
    results.sort(key=lambda x: (-x[0], -x[1]))
    return [entry for _, _, entry in results[:limit]]


def create_app(data_dir: Path = Path("data/output")) -> Any:
    """Create and configure the FastAPI application."""
    try:
        from fastapi import FastAPI, Query
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError:
        raise ImportError("FastAPI is required. Install with: pip install fastapi uvicorn")

    app = FastAPI(
        title="HinglishKosh API",
        description="Hinglish-English Dictionary API (हिंग्लिशकोश)",
        version="1.0.0",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Load dictionary on startup
    @app.on_event("startup")
    async def startup():
        _load_dictionary(data_dir)

    @app.get("/health")
    async def health():
        return {"status": "ok", "entries_loaded": len(_dictionary)}

    @app.get("/stats")
    async def stats():
        return {
            "name": _metadata.get("name", "HinglishKosh"),
            "version": _metadata.get("version", "unknown"),
            "total_entries": _metadata.get("total_entries", len(_dictionary)),
            "sources": _metadata.get("sources", []),
            "pos_distribution": _metadata.get("pos_distribution", {}),
        }

    @app.get("/lookup")
    async def lookup(
        word: str = Query(..., description="Word to look up (Hindi or Roman)"),
        safe: bool = Query(False, description="If true, use pre-filtered safe dataset"),
        min_confidence: float = Query(
            0.0, ge=0.0, le=1.0, description="Minimum confidence score"
        ),
        limit: int = Query(10, ge=1, le=100),
    ):
        data = _safe_dictionary if safe else _dictionary
        use_index = not safe  # index is built from full dict only
        results = _fuzzy_search(
            word, limit=limit, dictionary=data, use_index=use_index,
            min_confidence=min_confidence,
        )

        return {
            "query": word,
            "results": results,
            "count": len(results),
        }

    @app.get("/search")
    async def search(
        q: str = Query(..., description="Search query"),
        safe: bool = Query(False, description="If true, use pre-filtered safe dataset"),
        min_confidence: float = Query(
            0.0, ge=0.0, le=1.0, description="Minimum confidence score"
        ),
        limit: int = Query(20, ge=1, le=100),
    ):
        data = _safe_dictionary if safe else _dictionary
        results = _fuzzy_search(
            q, limit=limit, dictionary=data, min_confidence=min_confidence,
        )

        return {
            "query": q,
            "results": results,
            "count": len(results),
        }

    return app


def main():
    """Run the API server."""
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
