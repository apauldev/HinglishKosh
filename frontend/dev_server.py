"""Local dev server for HinglishKosh frontend.

Simulates Cloudflare Pages Functions using local SQLite DB.
Usage:
    python frontend/dev_server.py
    # Open http://localhost:8000
"""

from __future__ import annotations

import json
import logging
import mimetypes
import os
import sqlite3
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = FRONTEND_DIR / "public"
DB_PATH = FRONTEND_DIR / "hinglishkosh.db"

SAFE_THRESHOLD = 0.5

TAILWIND_CONFIG = r'''tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "tertiary-fixed": "#e0e3e5",
        "surface-container-highest": "#d3e4fe",
        "inverse-surface": "#213145",
        "primary-fixed": "#e1e0ff",
        "primary-container": "#6063ee",
        "secondary-container": "#dae2fd",
        "on-secondary-container": "#5c647a",
        "surface-container-low": "#eff4ff",
        "on-error": "#ffffff",
        "on-background": "#0b1c30",
        "tertiary-fixed-dim": "#c4c7c9",
        "on-secondary": "#ffffff",
        "on-secondary-fixed": "#131b2e",
        "on-surface": "#0b1c30",
        "error-container": "#ffdad6",
        "surface-bright": "#f8f9ff",
        "on-tertiary-fixed-variant": "#444749",
        "surface": "#f8f9ff",
        "on-tertiary-fixed": "#191c1e",
        "surface-dim": "#cbdbf5",
        "on-tertiary-container": "#fbfdff",
        "surface-container-lowest": "#ffffff",
        "inverse-on-surface": "#eaf1ff",
        "inverse-primary": "#c0c1ff",
        "on-primary": "#ffffff",
        "outline": "#767586",
        "surface-container": "#e5eeff",
        "primary": "#4648d4",
        "secondary-fixed": "#dae2fd",
        "error": "#ba1a1a",
        "secondary-fixed-dim": "#bec6e0",
        "on-primary-fixed": "#07006c",
        "on-primary-fixed-variant": "#2f2ebe",
        "tertiary-container": "#727577",
        "background": "#f8f9ff",
        "on-surface-variant": "#464554",
        "surface-container-high": "#dce9ff",
        "surface-tint": "#494bd6",
        "primary-fixed-dim": "#c0c1ff",
        "outline-variant": "#c7c4d7",
        "on-tertiary": "#ffffff",
        "on-primary-container": "#fffbff",
        "on-secondary-fixed-variant": "#3f465c",
        "tertiary": "#595c5e",
        "surface-variant": "#d3e4fe",
        "secondary": "#565e74",
        "on-error-container": "#93000a"
      },
      borderRadius: {
        DEFAULT: "0.125rem",
        lg: "0.25rem",
        xl: "0.5rem",
        full: "0.75rem"
      },
      spacing: {
        "stack-lg": "32px",
        "stack-md": "12px",
        "stack-sm": "4px",
        gutter: "24px",
        "container-max": "1440px",
        "margin-desktop": "48px",
        "margin-mobile": "16px"
      },
      fontFamily: {
        "hindi-entry": ["Noto Sans Devanagari"],
        "display-word": ["Inter"],
        "definition-num": ["Inter"],
        "label-caps": ["Inter"],
        "display-word-mobile": ["Inter"],
        "body-md": ["Inter"],
        "headline-md": ["Inter"],
        "body-lg": ["Inter"]
      },
      fontSize: {
        "hindi-entry": ["42px", {lineHeight: "60px", fontWeight: "500"}],
        "display-word": ["48px", {lineHeight: "56px", letterSpacing: "-0.02em", fontWeight: "700"}],
        "definition-num": ["14px", {lineHeight: "20px", fontWeight: "700"}],
        "label-caps": ["12px", {lineHeight: "16px", letterSpacing: "0.05em", fontWeight: "600"}],
        "display-word-mobile": ["36px", {lineHeight: "40px", letterSpacing: "-0.02em", fontWeight: "700"}],
        "body-md": ["16px", {lineHeight: "24px", fontWeight: "400"}],
        "headline-md": ["24px", {lineHeight: "32px", fontWeight: "600"}],
        "body-lg": ["18px", {lineHeight: "28px", fontWeight: "400"}]
      }
    }
  }
}'''


class HinglishHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves static files and handles API/word routes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        params = urllib.parse.parse_qs(parsed.query)

        # Route to handlers
        if path.startswith("/api/"):
            self.handle_api(path, params)
        elif path.startswith("/word/"):
            self.handle_word(path)
        elif path.startswith("/search"):
            self.handle_search(params)
        elif path.startswith("/about"):
            self.serve_static("about.html")
        else:
            self.serve_static(path.lstrip("/") or "index.html")

    # ─── API Handlers ───

    def handle_api(self, path: str, params: dict):
        endpoint = path.replace("/api/", "")
        try:
            if endpoint == "lookup":
                data = self.api_lookup(params)
            elif endpoint == "search":
                data = self.api_search(params)
            elif endpoint == "suggest":
                data = self.api_suggest(params)
            elif endpoint == "stats":
                data = self.api_stats()
            else:
                self.send_json({"error": "Unknown endpoint"}, 404)
                return
            self.send_json(data)
        except Exception as e:
            logger.error("API error: %s", e)
            self.send_json({"error": str(e)}, 500)

    def api_lookup(self, params: dict) -> dict:
        word = params.get("word", [""])[0]
        safe = params.get("safe", ["false"])[0] == "true"
        limit = min(int(params.get("limit", ["10"])[0]), 50)

        if not word.strip():
            return {"error": "Missing word parameter"}

        db = get_db()
        results = db.execute(
            "SELECT * FROM entries WHERE word_hindi = ? OR word_hinglish_roman = ? LIMIT ?",
            (word, word.lower(), limit),
        ).fetchall()
        entries = [dict(r) for r in results]

        if not entries:
            like = f"%{word}%"
            results = db.execute(
                "SELECT * FROM entries WHERE word_hindi LIKE ? OR word_hinglish_roman LIKE ? LIMIT ?",
                (like, like, limit),
            ).fetchall()
            entries = [dict(r) for r in results]

        if safe:
            entries = [e for e in entries if e.get("severity_score", 0) < SAFE_THRESHOLD]

        return {"query": word, "count": len(entries), "results": entries}

    def api_search(self, params: dict) -> dict:
        q = params.get("q", [""])[0]
        safe = params.get("safe", ["false"])[0] == "true"
        limit = min(int(params.get("limit", ["20"])[0]), 100)

        if not q.strip():
            return {"error": "Missing search query"}

        db = get_db()
        fts_query = " ".join(t + "*" for t in q.strip().split())
        try:
            results = db.execute(
                """SELECT e.*, rank FROM entries_fts f
                JOIN entries e ON e.rowid = f.rowid
                WHERE entries_fts MATCH ? ORDER BY rank LIMIT ?""",
                (fts_query, limit),
            ).fetchall()
            entries = [dict(r) for r in results]
            fallback = False
        except sqlite3.OperationalError:
            like = f"%{q.strip()}%"
            results = db.execute(
                "SELECT * FROM entries WHERE word_hindi LIKE ? OR word_hinglish_roman LIKE ? OR definition LIKE ? LIMIT ?",
                (like, like, like, limit),
            ).fetchall()
            entries = [dict(r) for r in results]
            fallback = True

        if safe:
            entries = [e for e in entries if e.get("severity_score", 0) < SAFE_THRESHOLD]

        return {"query": q, "count": len(entries), "results": entries, "fallback": fallback}

    def api_suggest(self, params: dict) -> dict:
        q = params.get("q", [""])[0]
        limit = min(int(params.get("limit", ["8"])[0]), 20)

        if not q.strip() or len(q.strip()) < 1:
            return {"suggestions": []}

        db = get_db()
        query = q.strip()
        results = db.execute(
            """SELECT word_hindi, word_hinglish_roman FROM entries
            WHERE word_hinglish_roman LIKE ? OR word_hindi LIKE ?
            GROUP BY word_hinglish_roman
            ORDER BY
                CASE WHEN word_hinglish_roman = ? THEN 0 WHEN word_hindi = ? THEN 1
                     WHEN word_hinglish_roman LIKE ? THEN 2 ELSE 3 END,
                LENGTH(word_hinglish_roman) ASC
            LIMIT ?""",
            (f"{query}%", f"{query}%", query, query, f"{query}%", limit),
        ).fetchall()
        return {"query": q, "suggestions": [dict(r) for r in results]}

    def api_stats(self) -> dict:
        db = get_db()
        total = db.execute("SELECT COUNT(*) as count FROM entries").fetchone()
        safe = db.execute("SELECT COUNT(*) as count FROM entries WHERE severity_score < 0.5").fetchone()
        toxic = db.execute("SELECT COUNT(*) as count FROM entries WHERE severity_score >= 0.5").fetchone()
        relations = db.execute("SELECT COUNT(*) as count FROM related_words").fetchone()
        sources = db.execute(
            "SELECT source, COUNT(*) as count FROM entries GROUP BY source ORDER BY count DESC"
        ).fetchall()
        pos = db.execute(
            "SELECT part_of_speech, COUNT(*) as count FROM entries WHERE part_of_speech != '' GROUP BY part_of_speech ORDER BY count DESC LIMIT 15"
        ).fetchall()
        return {
            "total_entries": total["count"],
            "safe_entries": safe["count"],
            "toxic_entries": toxic["count"],
            "total_relation_links": relations["count"],
            "sources": [dict(r) for r in sources],
            "pos_distribution": [dict(r) for r in pos],
        }

    # ─── Word Page Handler (SSR HTML) ───

    def handle_word(self, path: str):
        slug = urllib.parse.unquote(path.replace("/word/", "").strip("/"))
        if not slug:
            self.serve_static("404.html", 404)
            return

        db = get_db()
        entry = db.execute(
            "SELECT * FROM entries WHERE word_hinglish_roman = ? OR word_hindi = ? LIMIT 1",
            (slug, slug),
        ).fetchone()

        if not entry:
            entry = db.execute(
                "SELECT * FROM entries WHERE word_hinglish_roman LIKE ? OR word_hindi LIKE ? LIMIT 1",
                (f"%{slug}%", f"%{slug}%"),
            ).fetchone()
            if entry:
                new_slug = entry["word_hinglish_roman"] or entry["word_hindi"]
                self.send_response(302)
                self.send_header("Location", f"/word/{urllib.parse.quote(new_slug)}")
                self.end_headers()
                return

            self.serve_static("404.html", 404)
            return

        html = self._render_word_page(entry)
        self.send_html(html)

    def _render_word_page(self, entry) -> str:
        if not isinstance(entry, dict):
            entry = dict(entry)
        hindi = html_escape(entry["word_hindi"] or "")
        roman = html_escape(entry["word_hinglish_roman"] or "")
        definition = entry["definition"] or ""
        pos = html_escape(entry["part_of_speech"] or "")
        source = html_escape(entry["source"] or "")
        example = entry["example_sentence"] or ""
        severity = entry["severity_score"] or 0
        is_toxic = severity >= SAFE_THRESHOLD

        def_en = entry.get("definition_en") or ""
        def_hinglish = entry.get("definition_hinglish") or ""
        is_wordnet = entry.get("source") == "WordNet"

        title = f"{hindi} ({roman}) — {definition[:80]}"

        db = get_db()
        related = {}
        for rel_type in ("same_synset", "broader", "narrower"):
            rows = db.execute(
                """SELECT e.word_hindi, e.word_hinglish_roman FROM related_words r
                JOIN entries e ON e.id = r.related_entry_id
                WHERE r.entry_id = ? AND r.relation_type = ? ORDER BY e.word_hinglish_roman LIMIT 15""",
                (entry["id"], rel_type),
            ).fetchall()
            if rows:
                related[rel_type] = [dict(r) for r in rows]

        # ─── Definition cards ───
        def_cards = ""
        if def_en:
            def_cards += f'''<div class="premium-card p-6 rounded-xl border-l-4 border-l-primary">
<div class="flex items-center gap-2 mb-3">
<span class="px-2 py-0.5 bg-primary-container text-on-primary-container rounded font-label-caps text-[10px] tracking-widest uppercase">English</span>
</div>
<p class="font-body-lg text-body-lg text-on-surface leading-relaxed">{html_escape(def_en)}</p>
</div>'''
        if def_hinglish:
            def_cards += f'''<div class="premium-card p-6 rounded-xl border-l-4 border-l-tertiary">
<div class="flex items-center gap-2 mb-3">
<span class="px-2 py-0.5 bg-tertiary-container text-on-tertiary-container rounded font-label-caps text-[10px] tracking-widest uppercase">Hinglish</span>
</div>
<p class="font-body-lg text-body-lg text-on-surface leading-relaxed italic">{html_escape(def_hinglish)}</p>
</div>'''
        if definition and is_wordnet:
            def_cards += f'''<div class="premium-card p-6 rounded-xl border-l-4 border-l-secondary">
<div class="flex items-center gap-2 mb-3">
<span class="px-2 py-0.5 bg-secondary-container text-on-secondary-container rounded font-label-caps text-[10px] tracking-widest uppercase">Hindi</span>
</div>
<div class="pl-4 border-l-2 border-primary">
<p class="font-hindi-entry text-2xl text-on-surface leading-normal">{html_escape(definition)}</p>
</div>
</div>'''
        elif definition and not is_wordnet:
            def_cards += f'''<div class="premium-card p-6 rounded-xl border-l-4 border-l-secondary">
<div class="flex items-center gap-2 mb-3">
<span class="px-2 py-0.5 bg-secondary-container text-on-secondary-container rounded font-label-caps text-[10px] tracking-widest uppercase">Definition</span>
</div>
<p class="font-body-lg text-body-lg text-on-surface leading-relaxed">{html_escape(definition)}</p>
</div>'''

        # ─── Usage example ───
        ex_html = ""
        if example:
            ex_html = f'''<section class="mb-16">
<h3 class="font-label-caps text-label-caps text-outline mb-4 uppercase tracking-widest">Usage Context</h3>
<blockquote class="relative p-10 bg-surface-container-low rounded-xl border-y border-outline-variant overflow-hidden">
<span class="material-symbols-outlined absolute -top-2 -left-2 text-surface-container-high text-8xl opacity-50 pointer-events-none select-none">format_quote</span>
<p class="relative z-10 font-body-lg text-body-lg md:text-2xl text-on-surface italic leading-relaxed text-center">{html_escape(example)}</p>
</blockquote>
</section>'''

        # ─── Related terms ───
        def chip_row(items, icon, label, color_class, hover_bg):
            if not items:
                return ""
            chips = ""
            for r in items:
                uri = urllib.parse.quote(r["word_hinglish_roman"] or r["word_hindi"])
                r_roman = html_escape(r["word_hinglish_roman"] or "")
                r_hindi = html_escape(r["word_hindi"] or "")
                chip_label = f"{r_roman} ({r_hindi})" if r_roman and r_hindi else r_roman or r_hindi
                chips += f'''<a class="px-3 py-1 bg-surface-container text-on-surface-variant hover:{hover_bg} transition-colors rounded-full text-sm font-medium border border-outline-variant" href="/word/{html_escape(uri)}">{chip_label}</a>'''
            return f'''<div class="premium-card p-6 rounded-xl flex flex-col gap-4">
<div class="flex items-center gap-2 {color_class}">
<span class="material-symbols-outlined">{icon}</span>
<h4 class="font-label-caps text-label-caps uppercase tracking-wider">{label}</h4>
</div>
<div class="flex flex-wrap gap-2">{chips}</div>
</div>'''

        related_html = ""
        sections = ""
        sections += chip_row(related.get("same_synset", []), "sync_alt", "Synonyms", "text-primary", "bg-primary-fixed-dim")
        sections += chip_row(related.get("broader", []), "expand_less", "Broader Terms", "text-secondary", "bg-secondary-fixed-dim")
        sections += chip_row(related.get("narrower", []), "expand_more", "Narrower Terms", "text-tertiary", "bg-tertiary-fixed-dim")
        if sections:
            related_html = f'<section class="grid grid-cols-1 md:grid-cols-3 gap-gutter mb-16">{sections}</section>'

        # ─── POS / source badges ───
        badges = ""
        if pos:
            badges += f'<span class="px-3 py-1 bg-secondary-container text-on-secondary-container rounded-full font-label-caps text-label-caps border border-outline-variant">{pos}</span>'
        if source:
            badges += f'<span class="px-3 py-1 bg-surface-container-high text-on-surface-variant rounded-full font-label-caps text-label-caps border border-outline-variant">{source}</span>'
        if is_toxic:
            badges += f'<span class="px-3 py-1 bg-error-container text-on-error rounded-full font-label-caps text-label-caps border border-outline-variant">Flagged</span>'

        return f'''<!DOCTYPE html>
<html class="light" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{html_escape(title)} — HinglishKosh</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Devanagari:wght@400;500;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script>{TAILWIND_CONFIG}</script>
<style>
.material-symbols-outlined {{ font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; vertical-align: middle; }}
body {{ background-color: #f8fafc; }}
.premium-card {{ background-color: #ffffff; border: 1px solid #e2e8f0; transition: box-shadow 0.2s ease-in-out; }}
.premium-card:hover {{ box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05); }}
</style>
<link rel="stylesheet" href="/style.css"/>
</head>
<body class="font-body-md text-on-surface bg-background antialiased selection:bg-primary-fixed-dim">
<header class="bg-surface dark:bg-on-background border-b border-outline-variant dark:border-on-surface-variant sticky top-0 z-50">
<div class="flex justify-between items-center w-full px-margin-mobile md:px-margin-desktop py-4 max-w-container-max mx-auto">
<div class="flex items-center gap-8">
<a class="flex items-center gap-2.5 group" href="/" aria-label="HinglishKosh home">
<svg viewBox="0 0 36 36" class="h-9 w-9 shrink-0">
<defs>
<linearGradient id="logo-g" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
<stop stop-color="#4648d4"/>
<stop offset="1" stop-color="#7c3aed"/>
</linearGradient>
</defs>
<rect width="36" height="36" rx="9" fill="url(#logo-g)"/>
<text x="18" y="24" text-anchor="middle" font-family="system-ui,-apple-system,sans-serif" font-weight="700" font-size="17" fill="white">हिं</text>
</svg>
<div class="flex flex-col leading-tight">
<span class="text-base font-bold tracking-tight text-on-surface dark:text-[#e6e1e5]">हिंग्लिशकोश</span>
<span class="text-[11px] font-medium tracking-wider text-on-surface-variant dark:text-[#cac4d0] uppercase">HinglishKosh</span>
</div>
</a>
<nav class="hidden md:flex gap-6">
<a class="text-primary dark:text-primary-fixed font-bold border-b-2 border-primary dark:border-primary-fixed pb-1 font-label-caps text-label-caps" href="/">Home</a>
<a class="text-on-surface-variant dark:text-outline-variant hover:text-primary-container dark:hover:text-primary-fixed-dim transition-colors font-label-caps text-label-caps" href="/about">About</a>
</nav>
</div>
<div class="flex-1 max-w-md mx-8 hidden md:block">
<form action="/search" method="get" role="search" class="relative">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">search</span>
<input id="search-input" class="w-full pl-10 pr-4 py-2 bg-surface-container-lowest border border-outline-variant rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none font-body-md text-body-md" name="q" placeholder="Search for a word..." type="text"/>
<div id="suggestions" class="suggestions" hidden></div>
</form>
</div>
<div class="flex items-center gap-4">
<button id="theme-toggle" class="text-on-surface-variant p-2 rounded-full hover:bg-surface-container-high transition-colors" aria-label="Toggle theme">
<span class="material-symbols-outlined">dark_mode</span>
</button>
</div>
</div>
</header>
<main class="max-w-4xl mx-auto px-margin-mobile md:px-margin-desktop py-12 min-h-screen">
<section class="mb-stack-lg border-b border-outline-variant pb-stack-lg">
<div class="flex flex-col md:flex-row md:items-baseline justify-between gap-4">
<div class="flex flex-col gap-2">
<h1 class="font-display-word text-display-word-mobile md:text-display-word text-on-surface">{roman}</h1>
<div class="font-hindi-entry text-hindi-entry text-on-surface-variant leading-none">{hindi}</div>
</div>
<div class="flex gap-2 flex-wrap">
{badges}
</div>
</div>
</section>
<!-- TODO: pronunciation/phonetic notation — use a Hindi LLM to generate later
<div class="mt-stack-md flex items-center gap-2 text-outline font-body-md">
  <span class="font-definition-num text-definition-num">PHONETIC</span>
  <span class="font-mono text-sm tracking-wide">/placeholder/</span>
  <button class="text-primary hover:scale-110 transition-transform" aria-label="Listen to pronunciation">
    <span class="material-symbols-outlined text-2xl">volume_up</span>
  </button>
</div>
-->
<section class="space-y-stack-lg mb-16">
<div class="flex items-center gap-4 mb-stack-md">
<h2 class="font-headline-md text-headline-md text-on-surface">Definitions</h2>
<div class="h-px flex-1 bg-outline-variant"></div>
</div>
{def_cards}
</section>
{ex_html}
{related_html}
</main>
<footer class="bg-surface-container-low dark:bg-on-background border-t border-outline-variant dark:border-on-surface-variant">
<div class="flex flex-col md:flex-row justify-between items-start md:items-center w-full px-margin-mobile md:px-margin-desktop py-stack-lg max-w-container-max mx-auto gap-8">
<div class="flex flex-col gap-4">
<div class="flex items-center gap-2.5">
<svg viewBox="0 0 36 36" class="h-9 w-9 shrink-0">
<rect width="36" height="36" rx="9" fill="url(#logo-g)"/>
<text x="18" y="24" text-anchor="middle" font-family="system-ui,-apple-system,sans-serif" font-weight="700" font-size="17" fill="white">हिं</text>
</svg>
<span class="font-display-word text-headline-md text-primary dark:text-primary-fixed">हिंग्लिशकोश</span>
</div>
<p class="text-on-secondary-container dark:text-secondary-fixed-dim max-w-sm font-body-md text-body-md">HinglishKosh — {source} entry.</p>
<div class="text-on-secondary-container dark:text-secondary-fixed-dim font-label-caps text-label-caps mt-4">© <span id="cYear">2024</span> HinglishKosh · GPL v3</div>
</div>
<div class="grid grid-cols-2 gap-12 md:flex md:gap-16">
<div class="flex flex-col gap-3">
<span class="font-label-caps text-label-caps font-bold text-on-surface mb-2 dark:text-[#e6e1e5]">PROJECT</span>
<a class="font-body-md text-body-md text-on-secondary-container dark:text-secondary-fixed-dim hover:underline decoration-primary transition-all" href="/about">About</a>
<a class="font-body-md text-body-md text-on-secondary-container dark:text-secondary-fixed-dim hover:underline decoration-primary transition-all" href="https://github.com/apauldev/HinglishKosh">GitHub</a>
<a class="font-body-md text-body-md text-on-secondary-container dark:text-secondary-fixed-dim hover:underline decoration-primary transition-all" href="https://github.com/apauldev/HinglishKosh/blob/main/LICENSE">License</a>
</div>
<div class="flex flex-col gap-3">
<span class="font-label-caps text-label-caps font-bold text-on-surface mb-2 dark:text-[#e6e1e5]">COMMUNITY</span>
<a class="font-body-md text-body-md text-on-secondary-container dark:text-secondary-fixed-dim hover:underline decoration-primary transition-all" href="https://github.com/apauldev/HinglishKosh/issues">Feedback</a>
<a class="font-body-md text-body-md text-on-secondary-container dark:text-secondary-fixed-dim hover:underline decoration-primary transition-all" href="https://github.com/apauldev/HinglishKosh">Contribute</a>
</div>
</div>
</div>
</footer>
<script src="/app.js"></script>
</body>
</html>'''

    # ─── Search Page Handler ───

    def handle_search(self, params: dict):
        q = params.get("q", [""])[0]
        safe = params.get("safe", ["false"])[0] == "true"
        limit = min(int(params.get("limit", ["20"])[0]), 100)
        active_pos = (params.get("pos", [""])[0] or "").strip().lower()

        results = []
        if q.strip():
            api_result = self.api_search({"q": [q], "safe": [str(safe).lower()], "limit": [str(limit)]})
            results = api_result.get("results", [])
            if active_pos:
                results = [r for r in results if (r.get("part_of_speech") or "").lower() == active_pos]

        title = f'"{q}" search results' if q else "Search"

        # Build sidebar POS filter links
        all_counts = {}
        for e in self.api_search({"q": [q], "safe": [str(safe).lower()], "limit": [str(limit)]}).get("results", []):
            pos = e.get("part_of_speech") or "other"
            all_counts[pos] = all_counts.get(pos, 0) + 1
        total_all = sum(all_counts.values())
        total = len(results)
        base_url = f"/search?q={urllib.parse.quote(q)}" if q else "/search"

        pos_filters = ""
        all_cls = "font-body-md text-body-md text-primary font-bold" if not active_pos else "font-body-md text-body-md text-on-surface-variant"
        pos_filters += f'<li><a href="{html_escape(base_url)}" class="{all_cls}">All Results ({total_all})</a></li>'
        for pos_name in sorted(all_counts.keys()):
            cnt = all_counts[pos_name]
            esc_pos = html_escape(pos_name.capitalize())
            is_active = active_pos == pos_name
            cls = "font-body-md text-body-md text-primary font-bold" if is_active else "font-body-md text-body-md text-on-surface-variant hover:text-primary transition-colors"
            href = f"{base_url}&pos={urllib.parse.quote(pos_name)}"
            pos_filters += f'<li><a href="{html_escape(href)}" class="{cls}">{esc_pos} ({cnt})</a></li>'

        source_counts = {}
        for e in results:
            src = e.get("source") or "Unknown"
            source_counts[src] = source_counts.get(src, 0) + 1
        source_filters = ""
        for src_name in sorted(source_counts.keys()):
            cnt = source_counts[src_name]
            esc_src = html_escape(src_name)
            source_filters += f'<li><span class="font-body-md text-body-md text-on-surface-variant">{esc_src} ({cnt})</span></li>'

        # Build result cards
        results_html = ""
        if not results:
            q_esc = html_escape(q)
            q_hint = f' for <strong class="text-on-surface dark:text-[#e6e1e5]">{q_esc}</strong>' if q else ''
            results_html = f'<p class="font-body-lg text-body-lg text-on-surface-variant dark:text-[#cac4d0]">No results found{q_hint}. Try a different search term.</p>'
        else:
            for entry in results:
                h = html_escape(entry["word_hindi"] or "")
                r = html_escape(entry["word_hinglish_roman"] or "")
                def_en = html_escape(entry.get("definition_en") or "")
                def_hi = html_escape(entry.get("definition_hinglish") or "")
                d = html_escape(entry["definition"] or "")
                p = html_escape(entry["part_of_speech"] or "")
                src = entry["source"] or ""
                s = html_escape(src)
                severity = entry["severity_score"] or 0
                is_wordnet = src == "WordNet"
                uri = urllib.parse.quote(r or h)
                is_toxic = severity >= SAFE_THRESHOLD

                def_lines = []
                if def_en:
                    def_lines.append(f'<p class="font-body-lg text-body-lg text-on-surface dark:text-[#e6e1e5]"><span class="font-label-caps text-label-caps text-primary dark:text-[#c0c1ff] block mb-1">English</span>{def_en}</p>')
                if def_hi:
                    def_lines.append(f'<p class="font-body-lg text-body-lg text-on-surface dark:text-[#e6e1e5]"><span class="font-label-caps text-label-caps text-primary dark:text-[#c0c1ff] block mb-1">Hinglish</span>{def_hi}</p>')
                if d and is_wordnet:
                    def_lines.append(f'<p class="font-body-lg text-body-lg text-on-surface dark:text-[#e6e1e5]"><span class="font-label-caps text-label-caps text-primary dark:text-[#c0c1ff] block mb-1">Hindi</span>{d}</p>')
                elif d and not is_wordnet:
                    def_lines.append(f'<p class="font-body-lg text-body-lg text-on-surface dark:text-[#e6e1e5]">{d}</p>')
                def_line = '\n'.join(def_lines)
                toxic_border = ' border-l-2 border-l-red-400 dark:border-l-red-500' if is_toxic else ''

                results_html += f"""<article class="result-card bg-surface-container-lowest border border-outline-variant rounded-xl p-6 md:p-8 relative{toxic_border}">
<div class="flex flex-col md:flex-row gap-6">
<div class="flex-1 min-w-0">
<div class="flex flex-wrap items-baseline gap-4 mb-4">
<a href="/word/{uri}" class="hover:opacity-80 transition-opacity">
<h3 class="font-display-word text-display-word text-primary dark:text-[#c0c1ff]">{r or h}</h3>
</a>
{f'<span class="font-hindi-entry text-hindi-entry text-on-surface-variant dark:text-[#cac4d0]">{h}</span>' if h else ''}
{f'<span class="px-3 py-1 bg-secondary-container text-on-secondary-container font-label-caps text-label-caps rounded-full dark:bg-[#dae2fd]/20 dark:text-[#cac4d0]">{p}</span>' if p else ''}
</div>
<div class="space-y-3">
{def_line}
</div>
<div class="flex gap-4 mt-4">
<span class="text-on-surface-variant font-label-caps text-label-caps flex items-center gap-1 dark:text-[#cac4d0]">
<span class="material-symbols-outlined text-[16px]">menu_book</span> {s}
</span>
</div>
</div>
</div>
</article>"""

        tailwind_config = """
<script>
tailwind.config = {
  darkMode: 'class',
  theme: { extend: {
    colors: {
      'tertiary-fixed': '#e0e3e5', 'surface-container-highest': '#d3e4fe', 'inverse-surface': '#213145',
      'primary-fixed': '#e1e0ff', 'primary-container': '#6063ee', 'secondary-container': '#dae2fd',
      'on-secondary-container': '#5c647a', 'surface-container-low': '#eff4ff', 'on-error': '#ffffff',
      'on-background': '#0b1c30', 'tertiary-fixed-dim': '#c4c7c9', 'on-secondary': '#ffffff',
      'on-secondary-fixed': '#131b2e', 'on-surface': '#0b1c30', 'error-container': '#ffdad6',
      'surface-bright': '#f8f9ff', 'on-tertiary-fixed-variant': '#444749', 'surface': '#f8f9ff',
      'on-tertiary-fixed': '#191c1e', 'surface-dim': '#cbdbf5', 'on-tertiary-container': '#fbfdff',
      'surface-container-lowest': '#ffffff', 'inverse-on-surface': '#eaf1ff', 'inverse-primary': '#c0c1ff',
      'on-primary': '#ffffff', 'outline': '#767586', 'surface-container': '#e5eeff', 'primary': '#4648d4',
      'secondary-fixed': '#dae2fd', 'error': '#ba1a1a', 'secondary-fixed-dim': '#bec6e0',
      'on-primary-fixed': '#07006c', 'on-primary-fixed-variant': '#2f2ebe', 'tertiary-container': '#727577',
      'background': '#f8f9ff', 'on-surface-variant': '#464554', 'surface-container-high': '#dce9ff',
      'surface-tint': '#494bd6', 'primary-fixed-dim': '#c0c1ff', 'outline-variant': '#c7c4d7',
      'on-tertiary': '#ffffff', 'on-primary-container': '#fffbff', 'on-secondary-fixed-variant': '#3f465c',
      'tertiary': '#595c5e', 'surface-variant': '#d3e4fe', 'secondary': '#565e74', 'on-error-container': '#93000a'
    },
    borderRadius: { DEFAULT: '0.125rem', lg: '0.25rem', xl: '0.5rem', full: '0.75rem' },
    spacing: { 'stack-md': '12px', 'margin-desktop': '48px', 'stack-sm': '4px', 'gutter': '24px',
      'container-max': '1440px', 'stack-lg': '32px', 'margin-mobile': '16px' },
    fontFamily: { 'hindi-entry': ['Noto Sans Devanagari', 'sans-serif'], 'display-word': ['Inter', 'sans-serif'],
      'definition-num': ['Inter', 'sans-serif'], 'label-caps': ['Inter', 'sans-serif'],
      'display-word-mobile': ['Inter', 'sans-serif'], 'body-md': ['Inter', 'sans-serif'],
      'headline-md': ['Inter', 'sans-serif'], 'body-lg': ['Inter', 'sans-serif'] },
    fontSize: {
      'hindi-entry': ['42px', { lineHeight: '60px', fontWeight: '500' }],
      'display-word': ['48px', { lineHeight: '56px', letterSpacing: '-0.02em', fontWeight: '700' }],
      'definition-num': ['14px', { lineHeight: '20px', fontWeight: '700' }],
      'label-caps': ['12px', { lineHeight: '16px', letterSpacing: '0.05em', fontWeight: '600' }],
      'display-word-mobile': ['36px', { lineHeight: '40px', letterSpacing: '-0.02em', fontWeight: '700' }],
      'body-md': ['16px', { lineHeight: '24px', fontWeight: '400' }],
      'headline-md': ['24px', { lineHeight: '32px', fontWeight: '600' }],
      'body-lg': ['18px', { lineHeight: '28px', fontWeight: '400' }]
    }
  } }
}
</script>"""

        page = f"""<!DOCTYPE html>
<html class="light" lang="hi">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html_escape(title)} — HinglishKosh</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+Devanagari:wght@400;500;600;700&family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
{tailwind_config}
<style>
.material-symbols-outlined {{ font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }}
.result-card {{ transition: transform 0.2s ease, box-shadow 0.2s ease; }}
.result-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(15,23,42,0.05); }}
</style>
</head>
<body class="font-body-md text-on-surface bg-background antialiased selection:bg-primary-fixed-dim">
<header class="bg-surface dark:bg-on-background border-b border-outline-variant dark:border-on-surface-variant sticky top-0 z-50">
<div class="flex justify-between items-center w-full px-margin-mobile md:px-margin-desktop py-4 max-w-container-max mx-auto">
<div class="flex items-center gap-8">
<a class="flex items-center gap-2.5 group" href="/" aria-label="HinglishKosh home">
<svg viewBox="0 0 36 36" class="h-9 w-9 shrink-0">
<defs><linearGradient id="lg" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse"><stop stop-color="#4648d4"/><stop offset="1" stop-color="#7c3aed"/></linearGradient></defs>
<rect width="36" height="36" rx="9" fill="url(#lg)"/>
<text x="18" y="24" text-anchor="middle" font-family="system-ui,-apple-system,sans-serif" font-weight="700" font-size="17" fill="white">हिं</text>
</svg>
<div class="flex flex-col leading-tight">
<span class="text-base font-bold tracking-tight text-on-surface dark:text-[#e6e1e5]">हिंग्लिशकोश</span>
<span class="text-[11px] font-medium tracking-wider text-on-surface-variant dark:text-[#cac4d0] uppercase">HinglishKosh</span>
</div>
</a>
<nav class="hidden md:flex gap-6">
<a class="text-on-surface-variant dark:text-outline-variant hover:text-primary transition-colors font-label-caps text-label-caps" href="/">Home</a>
<a class="text-on-surface-variant dark:text-outline-variant hover:text-primary transition-colors font-label-caps text-label-caps" href="/about">About</a>
</nav>
</div>
<div class="flex-1 max-w-md mx-8 hidden md:block">
<form action="/search" method="get" role="search" class="relative">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline dark:text-[#cac4d0]">search</span>
<input id="search-input" name="q" value="{html_escape(q)}" class="w-full pl-10 pr-4 py-2 bg-surface-container-lowest border border-outline-variant rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none font-body-md text-body-md dark:bg-[#2b2930] dark:border-[#49454f] dark:text-[#e6e1e5] dark:placeholder:text-[#cac4d0]" placeholder="Search for a word..." type="text"/>
<div id="suggestions" class="suggestions" hidden></div>
</form>
</div>
<div class="flex items-center gap-4">
<button id="theme-toggle" class="text-on-surface-variant p-2 rounded-full hover:bg-surface-container-high transition-colors dark:text-[#cac4d0] dark:hover:bg-[#2b2930]" aria-label="Toggle theme">
<span class="material-symbols-outlined">dark_mode</span>
</button>
</div>
</div>
</header>

<main class="max-w-container-max mx-auto px-margin-mobile md:px-margin-desktop py-stack-lg">
<div class="grid grid-cols-1 md:grid-cols-12 gap-gutter">
<aside class="hidden md:block md:col-span-3 space-y-stack-lg">
<section>
<h3 class="font-label-caps text-label-caps text-on-surface-variant mb-4 dark:text-[#cac4d0]">PART OF SPEECH</h3>
<ul class="space-y-2">{pos_filters}</ul>
</section>
<section>
<h3 class="font-label-caps text-label-caps text-on-surface-variant mb-4 dark:text-[#cac4d0]">SOURCE</h3>
<ul class="space-y-2">{source_filters}</ul>
</section>
</aside>
<div class="md:col-span-9">
<div class="mb-stack-lg border-b border-outline-variant pb-stack-md flex justify-between items-end dark:border-[#49454f]">
<h2 class="font-headline-md text-headline-md text-on-surface dark:text-[#e6e1e5]">{f'Results for &lsquo;{html_escape(q)}&rsquo;' if q else 'Search'} <span class="text-on-surface-variant font-normal opacity-70 dark:text-[#cac4d0]">({total} match{"es" if total != 1 else ""})</span></h2>
</div>
<div class="space-y-gutter">{results_html}</div>
{f'''<div class="mt-stack-lg pt-stack-lg border-t border-outline-variant text-center dark:border-[#49454f]">
<p class="font-body-lg text-body-lg text-on-surface-variant mb-6 dark:text-[#cac4d0]">Can&rsquo;t find what you&rsquo;re looking for?</p>
<a href="/" class="inline-flex items-center gap-2 bg-primary text-on-primary font-label-caps text-label-caps px-8 py-4 rounded-full hover:bg-primary-container transition-all uppercase tracking-widest shadow-md dark:bg-[#c0c1ff] dark:text-[#1d1b20] dark:hover:bg-[#a8a9ff]">
Explore Home <span class="material-symbols-outlined">trending_flat</span>
</a>
</div>''' if not results else ''}
</div>
</div>
</main>

<footer class="bg-surface-container-low border-t border-outline-variant mt-stack-lg dark:bg-[#1d1b20] dark:border-[#49454f]">
<div class="flex flex-col md:flex-row justify-between items-center w-full px-margin-mobile md:px-margin-desktop py-stack-lg max-w-container-max mx-auto">
<div class="mb-8 md:mb-0 text-center md:text-left">
<div class="flex items-center gap-2.5 mb-2 justify-center md:justify-start">
<svg viewBox="0 0 36 36" class="h-7 w-7 shrink-0"><rect width="36" height="36" rx="9" fill="url(#lg)"/><text x="18" y="24" text-anchor="middle" font-family="system-ui,-apple-system,sans-serif" font-weight="700" font-size="17" fill="white">हिं</text></svg>
<span class="font-display-word text-headline-md text-primary dark:text-[#c0c1ff]">हिंग्लिशकोश</span>
</div>
<p class="font-label-caps text-label-caps text-on-secondary-container dark:text-[#cac4d0]">© <span id="cYear">2024</span> HinglishKosh · GPL v3</p>
</div>
<div class="flex flex-wrap justify-center gap-x-8 gap-y-4">
<a class="font-label-caps text-label-caps text-on-secondary-container hover:underline decoration-primary transition-all dark:text-[#cac4d0]" href="/about">About</a>
<a class="font-label-caps text-label-caps text-on-secondary-container hover:underline decoration-primary transition-all dark:text-[#cac4d0]" href="https://github.com/apauldev/HinglishKosh">GitHub</a>
<a class="font-label-caps text-label-caps text-on-secondary-container hover:underline decoration-primary transition-all dark:text-[#cac4d0]" href="https://github.com/apauldev/HinglishKosh/blob/main/LICENSE">License</a>
</div>
</div>
</footer>
<script src="/app.js"></script>
</body>
</html>"""
        self.send_html(page)

    # ─── Static File Serving ───

    def serve_static(self, filename: str, status: int = 200):
        filepath = PUBLIC_DIR / filename
        if not filepath.exists() or not filepath.is_file():
            filepath = PUBLIC_DIR / "404.html"
            status = 404

        content = filepath.read_bytes()
        ctype = mimetypes.guess_type(str(filepath))[0] or "application/octet-stream"
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    # ─── Response Helpers ───

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html: str, status: int = 200):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args):
        logger.info("  ⇨  %s", args[-1] if args else "")


def html_escape(s: str) -> str:
    if not s:
        return ""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def get_db() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise RuntimeError(
            f"Database not found at {DB_PATH}. Run:\n"
            f"  python frontend/src/seed/seed.py"
        )
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def main():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), HinglishHandler)
    print(f"\n  HinglishKosh dev server → http://localhost:{port}")
    print(f"  (Press Ctrl+C to stop)\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
