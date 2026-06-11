# HinglishKosh — Optimization Analysis

This document identifies performance bottlenecks, memory inefficiencies, and scalability limitations in the current codebase, along with concrete optimization strategies for each.

> **Before you optimize:** Profile first. 209K entries is small — a linear scan takes ~15ms, which is fine for most use cases. The recommendations below are ranked by practical impact, not theoretical perfection. Start with the "Do First" items; everything else can wait until you measure a real problem.

---

## 0. Prerequisites: Profile Before Optimizing

Before implementing any optimization, run profiling to confirm which bottlenecks are real:

```bash
# Profile the pipeline (build-time)
python -m cProfile -s cumulative -m src.processing.pipeline 2>&1 | head -40

# Profile the API (runtime)
python -m cProfile -s cumulative -c "from src.api.main import app" 2>&1 | head -40

# Quick memory check
python -m memory_profiler src/cli.py stats
```

This prevents over-engineering solutions for problems that don't exist at current scale.

---

## 1. Do First — Quick Wins (days, not weeks)

These are high-impact, low-effort changes that address real, measurable problems.

### 1a. Hash index for API exact lookup

**Problem:** `/lookup` does a linear scan of 209K entries for every query (~15ms).

**Fix:** Pre-build a `dict[str, list[int]]` at startup. Exact lookups become O(1).

```python
# Build once at load time
_lookup_index: dict[str, list[int]] = {}
for i, entry in enumerate(_dictionary):
    key = entry.get("word_hindi", "").lower().strip()
    _lookup_index.setdefault(key, []).append(i)
    key_roman = entry.get("word_hinglish_roman", "").lower().strip()
    _lookup_index.setdefault(key_roman, []).append(i)

# Lookup: O(1) — ~0.1ms instead of ~15ms
entry_indices = _lookup_index.get(query_lower, [])
```

**Impact:** 150x faster for exact lookups. Covers the most common use case.

### 1b. SQLite for CLI startup

**Problem:** `hinglish-dict lookup` loads a 150MB JSON file on every invocation. Startup takes 2-4 seconds.

**Fix:** Generate a SQLite `.db` during the pipeline. CLI queries it directly.

```python
# Pipeline adds this after writing JSON:
conn = sqlite3.connect("data/output/hinglish_dict.db")
# ... create FTS5 table, insert entries ...

# CLI loads instantly:
conn = sqlite3.connect("data/output/hinglish_dict.db")
```

**Impact:** CLI startup drops from 2-4s to <100ms. This is the most user-visible problem.

### 1c. Move `_COMMON_WORDS` to a data file

**Problem:** 600+ hardcoded entries in `transliterate.py` (~300 lines of string literals). Every new word requires a code change and recompilation.

**Fix:** Move to `data/common_words.json`. Load on first use, not at import time.

```json
{
  "नमस्ते": "namaste",
  "पानी": "paani",
  "चाय": "chai"
}
```

```python
_COMMON_WORDS: dict[str, str] = {}

def _load_common_words():
    global _COMMON_WORDS
    if not _COMMON_WORDS:
        path = Path(__file__).parent.parent.parent / "data" / "common_words.json"
        with open(path) as f:
            _COMMON_WORDS = json.load(f)
    return _COMMON_WORDS
```

**Impact:** Reduces `transliterate.py` from 925 lines to ~600. Makes romanization editable without code changes.

### 1d. Response caching for API

**Problem:** Common words like `पानी`, `प्यार`, `घर` are looked up repeatedly — each time scanning 209K entries.

**Fix:** Add an in-memory LRU cache.

```python
from cachetools import TTLCache

_lookup_cache = TTLCache(maxsize=1000, ttl=3600)

@app.get("/lookup")
async def lookup(word: str, safe: bool = False, limit: int = 10):
    cache_key = f"{word}:{safe}:{limit}"
    if cache_key in _lookup_cache:
        return _lookup_cache[cache_key]
    result = do_lookup(word, safe, limit)
    _lookup_cache[cache_key] = result
    return result
```

**Impact:** 100x faster for cache hits. Zero cost for cache misses.

---

## 2. Do Next — Architecture Improvements (1-2 weeks)

These improve code quality and reduce complexity, with performance as a side benefit.

### 2a. SQLite-backed API server

**Problem:** API loads 150MB JSON into ~700MB of Python dicts. Not a crisis at current scale, but unnecessary complexity.

**Fix:** Use SQLite FTS5 as the query backend. The pipeline already generates a `.db` file — the API just needs to use it.

```python
import sqlite3

conn = sqlite3.connect("data/output/hinglish_dict.db")

@app.get("/lookup")
async def lookup(word: str, safe: bool = True, limit: int = 10):
    rows = conn.execute(
        "SELECT * FROM dictionary WHERE word_hindi = ? OR word_hinglish_roman = ? LIMIT ?",
        (word, word, limit)
    ).fetchall()
    return format_results(rows)
```

**Impact:** Simpler architecture. RAM drops from ~700MB to ~10MB. Queries stay fast. But honestly — 700MB is fine on modern hardware. Do this for simplicity, not performance.

### 2b. Single-pass export pipeline

**Problem:** Pipeline writes JSON, then AOSP and SQLite exports read it back. Redundant I/O.

**Fix:** Run all exports during the main pipeline pass, after merge and before JSON write.

```python
# In pipeline.py, after merge + romanization:
aosp_dict_export(merged, output_dir / "hinglish.dict")
sqlite_export(merged, output_dir / "hinglish.db")
# Then write JSON
```

**Impact:** Eliminates one full read of the 150MB output. Cleaner pipeline flow.

### 2c. Parallel data loading

**Problem:** WordNet, Wiktionary, and supplemental loading runs sequentially, even though they're independent.

**Fix:** Load concurrently with `ThreadPoolExecutor`.

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    wordnet_future = executor.submit(load_wordnet, wordnet_dir)
    wiktionary_future = executor.submit(load_wiktionary, wiktionary_dir)
    supp_future = executor.submit(load_supplemental, supp_dir)

    wordnet_entries = wordnet_future.result()
    wiktionary_entries = wiktionary_future.result()
    supplemental_entries = supp_future.result()
```

**Impact:** ~3x faster data loading. Low effort, clean improvement.

### 2d. Batch ML inference for safety filter

**Problem:** `ToxicityClassifier` runs inference one entry at a time. HuggingFace pipelines are designed for batching.

**Fix:** Batch entries into groups of 32-64.

```python
for batch in batched(entries, 64):
    texts = [text_for(entry) for entry in batch]
    results = classifier.classify_batch(texts)
```

**Impact:** 5-20x faster safety filtering. Only matters if you're re-processing the full dataset regularly.

---

## 3. Do Later — Scaling Optimizations (when you measure a problem)

These are theoretically sound but premature for 209K entries. Implement only if profiling shows a real bottleneck.

### 3a. Trie for prefix search

**Problem:** Prefix/partial matching still does a linear scan.

**Fix:** Build a memory-compact trie via `datrie` or `pygtrie` over Hindi and Roman headwords.

**When to implement:** When you have >1M entries or measure >50ms prefix search latency. At 209K entries, linear scan is fine.

### 3b. Levenshtein automaton for typo tolerance

**Problem:** No typo-tolerant search (e.g., "chai" vs "chay").

**Fix:** Use `symspell` library — handles 100K+ dictionaries at sub-millisecond speeds.

**When to implement:** When users complain about typos. Not a current priority.

### 3c. Aho-Corasick for `iso_to_hinglish`

**Problem:** 20+ sequential regex passes in `iso_to_hinglish()`.

**Fix:** Single Aho-Corasick automaton pass via `pyahocorasick`.

**When to implement:** When you profile `iso_to_hinglish()` as a bottleneck (unlikely — these are short strings with ~20 patterns).

### 3d. Aho-Corasick for profanity matching

**Problem:** Per-word linear scan against profanity wordlist.

**Fix:** Single automaton pass over entire text.

**When to implement:** When profanity checking becomes a bottleneck (unlikely — wordlist matching is O(1) per word via set lookup).

### 3e. Non-crypto hash for dedup

**Problem:** `_definition_hash()` uses MD5, which is cryptographic and slower than necessary.

**Fix:** Replace with `xxhash.xxh64()` (~10x faster for short strings).

**When to implement:** When you're re-processing the full dataset regularly and dedup is measured as slow.

### 3f. Generator streaming for pipeline

**Problem:** Pipeline materializes entire merged list before romanization.

**Fix:** Use generator pipelines to overlap I/O with processing.

**When to implement:** When peak RAM during pipeline execution becomes a problem (unlikely for a batch job).

### 3g. Memory-mapped binary format

**Problem:** Full JSON deserialization on every load.

**Fix:** Replace with `struct` + `mmap` for on-demand paging.

**When to implement:** Never, unless you're deploying on embedded systems with <512MB RAM. SQLite already solves this.

---

## 4. Don't Bother — Premature Optimizations

These add complexity without measurable benefit at current scale.

### BK-tree for profanity filtering

Profanity wordlist matching is already O(1) per word via Python set lookup. A BK-tree adds complexity for no gain. The bottleneck (if any) is text splitting, not wordlist matching.

### String interning with `sys.intern()`

Python already interns short strings. The memory savings for 209K entries with repeated field values is negligible (~5-10MB). Not worth the code complexity.

### Lazy property access (`dict[key]` vs `dict.get()`)

The difference is microseconds per call. Across 209K entries, this adds up to seconds — but only during pipeline execution, which runs once. Not worth optimizing.

### Streaming JSON writer

`json.dump()` holding the full string in memory is ~80MB. On any modern machine, this is fine. Streaming adds complexity for no user-visible benefit.

---

## 5. Build-Time vs Runtime Costs

Understanding which optimizations matter depends on *when* the code runs:

| Phase | Runs when? | Current bottleneck | Worth optimizing? |
|---|---|---|---|
| Pipeline (build) | Once, during development | Merge fuzzy matching | Only if >5min |
| Safety filter | Once, during ML inference | Sequential per-entry | Yes, if re-processing |
| API (runtime) | Every request | Linear scan | **Yes — hash index** |
| CLI (runtime) | Every invocation | JSON load (2-4s) | **Yes — SQLite** |
| Export (build) | Once, during pipeline | JSON write | No — runs once |

**Key insight:** Build-time bottlenecks are tolerable — the pipeline runs once. Runtime bottlenecks (API, CLI) affect every user interaction and should be prioritized.

---

## 6. Bottleneck Summary

| Area | Current Cost | Recommended Fix | Priority | Effort |
|---|---|---|---|---|
| API exact lookup | O(n), ~15ms | Hash index | **Do First** | Low |
| CLI startup | 2-4s JSON load | SQLite backend | **Do First** | Low |
| Common words | 600 entries in code | Move to JSON file | **Do First** | Low |
| API caching | No caching | LRU cache | **Do First** | Low |
| API architecture | ~700MB RAM | SQLite backend | Do Next | Medium |
| Data loading | Sequential | Parallel load | Do Next | Low |
| Safety ML inference | Sequential | Batch inference | Do Next | Medium |
| Pipeline exports | Read-after-write | Single-pass | Do Next | Low |
| Prefix search | O(n) | Trie | Later | Medium |
| Typo tolerance | None | Symspell | Later | Medium |
| Transliteration | Per-call import | Module-level try | Later | Low |
| Dedup hash | MD5 | xxHash | Later | Low |
| Profanity matching | Per-word scan | Aho-Corasick | Later | Low |
| Memory format | JSON dicts | Memory-mapped | Don't bother | High |

**Top 3 actions:**
1. **Hash index for API lookups** — 150x faster, covers most usage
2. **SQLite for CLI startup** — fixes the most annoying UX problem
3. **Move `_COMMON_WORDS` to data file** — cleaner codebase, no recompilation for new words

---

## 7. Micro-Optimizations (Apply During Normal Development)

These are small code improvements to make during regular development, not as separate optimization tasks:

### Avoid repeated imports

In `transliterate()`, `import varnam` / `import indictrans` happens inside the function body. Move to module level with a flag:

```python
try:
    from varnam import varnam
    _VANNAM_AVAILABLE = True
except ImportError:
    _VANNAM_AVAILABLE = False
```

### Pre-compile regex patterns

Move inline `re.sub()` patterns in `iso_to_hinglish()` and `ProfanityMatcher._normalize()` to module-level `re.compile()` calls.

### SQLite export pragmas

For the SQLite export step, add performance pragmas:

```python
cursor.execute("PRAGMA synchronous = OFF")
cursor.execute("PRAGMA journal_mode = WAL")
cursor.execute("PRAGMA cache_size = -64000")  # 64 MB cache
# ... INSERT ...
cursor.execute("PRAGMA synchronous = NORMAL")  # Restore safety
```

These add up over 209K entries but aren't worth a dedicated optimization task.

---

## 8. What Not to Optimize (Yet)

- **Memory usage at 700MB** — fine on modern servers, not a crisis
- **Pipeline execution time** — runs once, not in a hot loop
- **JSON export size** — 80MB compact is acceptable
- **String lowercasing in search** — negligible cost
- **Fuzzy matching speed** — runs once during build, not runtime

The best optimization is the one that solves a problem you've actually measured. Start with profiling, implement the "Do First" items, and revisit this document when you have real data.
