"""FastAPI REST API for HinglishKosh dictionary lookups.

Endpoints:
    GET /lookup?word={word}&safe=true
    GET /search?q={query}&limit=20
    GET /stats
    GET /health
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Lazy-loaded dictionary data
_dictionary: list[dict[str, Any]] = []
_metadata: dict[str, Any] = {}


def _load_dictionary(data_dir: Path = Path("data/output")) -> None:
    """Load dictionary data from JSON file."""
    global _dictionary, _metadata

    json_file = data_dir / "hinglish_dictionary_v1.json"
    if not json_file.exists():
        logger.warning("Dictionary file not found: %s", json_file)
        return

    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)

    _metadata = data.get("meta", {})
    _dictionary = data.get("dictionary", [])
    logger.info("Loaded %d entries from %s", len(_dictionary), json_file)


def _fuzzy_search(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Simple fuzzy search across headwords and definitions."""
    query_lower = query.lower().strip()
    if not query_lower:
        return []

    results = []
    for entry in _dictionary:
        score = 0

        # Exact headword match (highest priority)
        if entry.get("word_hindi", "").lower() == query_lower:
            score = 100
        elif entry.get("word_hinglish_roman", "").lower() == query_lower:
            score = 95
        # Partial match in headword
        elif query_lower in entry.get("word_hindi", "").lower():
            score = 80
        elif query_lower in entry.get("word_hinglish_roman", "").lower():
            score = 75
        # Match in definition
        elif query_lower in entry.get("definition", "").lower():
            score = 50

        if score > 0:
            results.append((score, entry))

    results.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in results[:limit]]


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
        safe: bool = Query(False, description="If true, filter out toxic entries"),
        limit: int = Query(10, ge=1, le=100),
    ):
        results = _fuzzy_search(word, limit=limit)

        if safe:
            results = [r for r in results if r.get("severity_score", 0) < 0.5]

        return {
            "query": word,
            "results": results,
            "count": len(results),
        }

    @app.get("/search")
    async def search(
        q: str = Query(..., description="Search query"),
        safe: bool = Query(False),
        limit: int = Query(20, ge=1, le=100),
    ):
        results = _fuzzy_search(q, limit=limit)

        if safe:
            results = [r for r in results if r.get("severity_score", 0) < 0.5]

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
