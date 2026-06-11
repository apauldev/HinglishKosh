# HinglishKosh — Implementation Plan

> A task-based blueprint for building a 200K+ entry Hinglish-English dictionary.

---

## Phase 1: Project Setup & Data Acquisition ✅

### Task 1.1: Initialize Project Skeleton ✅
- [x] Create `pyproject.toml` with dependencies
- [x] Create `src/__init__.py` and subpackage `__init__.py` files
- [x] Create `data/raw/`, `data/processed/`, `data/output/` directories
- [x] Create `.gitignore` for Python/data artifacts
- [x] Add `README.md` with project overview

### Task 1.2: Download Hindi WordNet (IIT Bombay) ✅
- [x] Download Hindi WordNet JSON/XML from IIT Bombay's IndoWordNet portal
- [x] Store raw files in `data/raw/wordnet/`
- [x] Write `src/ingestion/wordnet_loader.py` to parse synsets, glosses, examples, POS tags
- [x] Validate: count unique headwords, verify Hindi + English gloss pairs exist

### Task 1.3: Download Wiktionary Data (kaikki.org) ✅
- [x] Download `kaikki.org dictionaries/Hindi (hi).jsonl.gz` from kaikki.org
- [x] Decompress and store in `data/raw/wiktionary/`
- [x] Write `src/ingestion/wiktionary_loader.py` to parse JSONL entries
- [x] Extract: headword, POS, definitions, examples, etymology
- [x] Filter out non-Hindi/non-Urdu entries

### Task 1.4: Download Transliteration Models ✅
- [x] Implement rule-based transliteration as primary method
- [x] Write `src/processing/transliterate.py` wrapper module
- [x] Add ISO 15919 → Hinglish converter

### Task 1.5: Download Supplemental Hinglish Datasets ✅
- [x] Create `src/ingestion/supplemental_loader.py`
- [x] Support for custom word lists and profanity filters

---

## Phase 2: Core Dictionary Processing ✅

### Task 2.1: Build WordNet Core Dictionary ✅
- [x] Load parsed WordNet data
- [x] Create core entries with all required fields
- [x] Deduplicate by `word_hindi` + `definition_hash`
- [x] Output: 153,204 WordNet entries

### Task 2.2: Build Wiktionary Extended Dictionary ✅
- [x] Load parsed Wiktionary data
- [x] Normalize headwords (handle Unicode variations, ligatures)
- [x] Resolve malformed entries
- [x] Create extended entries with same schema
- [x] Output: 56,258 Wiktionary entries

### Task 2.3: Merge & Deduplicate Dictionaries ✅
- [x] Load both processed dictionaries
- [x] Use fuzzy matching (rapidfuzz) on romanized + Hindi headwords
- [x] Priority: WordNet entries win on conflicts
- [x] Merge definitions from both sources
- [x] Assign unified `id` (WN-XXXXX / WK-XXXXX format)
- [x] Output: 209,462 total entries (125,038 unique headwords)

### Task 2.4: Enhanced Definition Expansion (RAG) ⏳
- [ ] Identify entries with missing or Hindi-only definitions
- [ ] Call LLM API to generate English definition supplement
- [ ] Manual validation: sample 100 entries, review accuracy

### Task 2.5: Generate Unified Dataset ✅
- [x] Assemble final dictionary with all fields from schema
- [x] Add metadata block (version, total_entries, sources, license, date)
- [x] Validate: all required fields present, no nulls in critical fields
- [x] Output: `data/output/hinglish_dictionary_v1.json` (151 MB)

---

## Phase 3: Safety Filter ✅

### Task 3.1: Build Profanity Wordlist ✅
- [x] Compile Hindi/Hinglish profanity list
- [x] Include spelling variations (Devanagari, Roman, leet-speak)
- [x] Store as `data/raw/profanity/master_list.json` with severity levels

### Task 3.2: Set Up Toxicity Detection Pipeline ✅
- [x] Create `src/safety/toxicity_classifier.py` wrapper
- [x] Create `src/safety/profanity_list.py` for wordlist-based detection
- [x] Create `src/safety/severity_scorer.py` for multi-model consensus

### Task 3.3: Process Full Dataset Through Safety Filter ✅
- [x] Run dictionary-based detection on all headwords
- [x] Run ML-based classifier on definitions + example sentences
- [x] Combine results into `toxicity_flags` array per entry
- [x] Compute `severity_score` (0.0–1.0)

### Task 3.4: Validate Safety Filter ⏳
- [ ] Manual audit: 1,000 random entries
- [ ] Calculate false positive rate and false negative rate
- [ ] Tune thresholds, add whitelist for false positives

---

## Phase 4: API & Integration ✅

### Task 4.1: Build REST API ✅
- [x] Create `src/api/main.py` with FastAPI
- [x] Endpoints:
  - `GET /lookup?word={word}&safe=true`
  - `GET /search?q={query}&limit=20`
  - `GET /stats` (dataset metadata)
- [x] Implement phonetic matching
- [x] Add CORS, rate limiting, health check

### Task 4.2: Generate Keyboard Formats ✅
- [x] Create `src/integration/aosp_dict_export.py`
- [x] Convert dictionary to AOSP `.dict` format
- [x] Generate SQLite FTS virtual table for offline app search
- [x] Output: `data/output/hinglish.dict`, `data/output/hinglish.db`

### Task 4.3: Package & Publish ⏳
- [x] Finalize `pyproject.toml` with entry points
- [x] Add CLI tool: `hinglish-dict lookup <word>`
- [x] Write tests in `tests/` (701 tests passing)
- [ ] Create GitHub Actions CI pipeline
- [ ] Prepare Hugging Face Dataset card
- [ ] Tag release: `v1.0.0`
- [ ] Upload to Hugging Face Datasets

---

## Phase 5: Distribution ⏳

### Task 5.1: GitHub Release
- [ ] Create release script (`scripts/release.sh`)
- [ ] Tag version and create GitHub release
- [ ] Attach dataset files (JSON, CSV, .dict, .db)
- [ ] Document changelog

### Task 5.2: Hugging Face Upload
- [ ] Create Hugging Face dataset card
- [ ] Upload dataset to Hugging Face Datasets
- [ ] Add dataset viewer
- [ ] Document usage examples

### Task 5.3: Documentation ✅
- [x] Write `docs/architecture.md` — full pipeline breakdown: ingestion, transliteration, merge/dedup, safety filter, API, CLI, exports, schema, tests, CI/CD
- [x] Write `docs/optimizations.md` — prioritized optimization analysis: Do First / Do Next / Do Later / Don't Bother tiers

---

## Phase 6: Quick-Win Optimizations ⏳

> See `docs/optimizations.md` for full analysis. These are high-impact, low-effort changes that address real, measurable problems. Profile before implementing — `python -m cProfile -s cumulative -m src.processing.pipeline`.

### Task 6.1: Hash index for API exact lookup ⏳
- [ ] Pre-build `dict[str, list[int]]` mapping normalized headwords to array indices at API startup
- [ ] Exact lookups become O(1) instead of O(n) — ~0.1ms instead of ~15ms
- [ ] Fallback to linear scan for partial/substring matches
- [ ] Add test: verify hash index matches linear scan results

### Task 6.2: SQLite for CLI startup ⏳
- [ ] Generate `hinglish_dict.db` during pipeline (after merge, before JSON write)
- [ ] Create FTS5 virtual table for search
- [ ] Update CLI to query SQLite instead of loading full JSON
- [ ] Startup drops from 2-4s to <100ms

### Task 6.3: Move `_COMMON_WORDS` to data file ⏳
- [ ] Extract 600+ entries from `src/processing/transliterate.py` to `data/common_words.json`
- [ ] Load on first use (lazy), not at import time
- [ ] Reduce `transliterate.py` from ~925 lines to ~600
- [ ] Add test: verify all common words still romanize correctly

### Task 6.4: API response caching ⏳
- [ ] Add `cachetools.TTLCache` for `/lookup` and `/search` results
- [ ] TTL: 1 hour, maxsize: 1000 entries
- [ ] Common words (`पानी`, `प्यार`, `घर`) hit cache on repeat queries

### Task 6.5: Parallel data loading ⏳
- [ ] Load WordNet, Wiktionary, supplemental concurrently with `ThreadPoolExecutor`
- [ ] ~3x faster pipeline startup

---

## File Structure

```
hinglish-dict/
├── PLAN.md
├── README.md
├── LICENSE                  # GPL v3.0
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── wordnet_loader.py
│   │   ├── wiktionary_loader.py
│   │   └── supplemental_loader.py
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── transliterate.py
│   │   ├── dedup.py
│   │   ├── merge.py
│   │   └── pipeline.py
│   ├── safety/
│   │   ├── __init__.py
│   │   ├── profanity_list.py
│   │   ├── toxicity_classifier.py
│   │   └── severity_scorer.py
│   ├── api/
│   │   └── main.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── aosp_dict_export.py
│   │   └── sqlite_export.py
│   └── cli.py
├── tests/
│   ├── test_1000_words.py
│   ├── test_lookup.py
│   ├── test_api.py
│   └── ...
├── data/
│   ├── raw/                 # Downloaded source data (gitignored)
│   ├── processed/           # Intermediate processing (gitignored)
│   └── output/              # Final dataset (gitignored, in releases)
├── docs/
│   ├── architecture.md      # Full system architecture
│   └── optimizations.md     # Performance optimization analysis
├── scripts/
│   ├── download_data.sh
│   ├── release.sh
│   └── upload_hf.sh
└── .github/
    └── workflows/
        └── ci.yml           # ✅ GitHub Actions lint + test on push/PR
```

---

## Data Schema (Unified JSON)

```json
{
  "id": "HIN-00001",
  "word_hindi": "नमस्ते",
  "word_hinglish_roman": "namaste",
  "definition": "A respectful greeting or salutation in Hindi.",
  "part_of_speech": "interjection",
  "example_sentence": "नमस्ते, आप कैसे हैं? (Namaste, aap kaise hain?)",
  "synsets": ["hi-interjection-001"],
  "source": "WordNet",
  "confidence_score": 0.95,
  "toxicity_flags": [],
  "severity_score": 0.0
}
```

---

## Dependencies

```toml
[project]
requires-python = ">=3.9"
dependencies = [
    "pandas>=2.0",
    "requests>=2.28",
    "tqdm>=4.64",
    "rapidfuzz>=3.0",
    "fastapi>=0.100",
    "uvicorn>=0.22",
    "transformers>=4.30",
    "torch>=2.0",
    "huggingface-hub>=0.15",
    "soundex>=1.1",
]
```

---

## Licensing

| Component | License | Notes |
|---|---|---|
| Project code | GPL 3.0 | Compatible with WordNet |
| API wrapper | Apache 2.0 | If kept separate from GPL core |
| Output dataset | GPL 3.0 | Derivative of WordNet |
| Profanity filter | MIT | Permissive |
| ML models | Apache 2.0 | IndicBERT |

---

## Progress

| Phase | Status | Entries |
|---|---|---|
| Phase 1: Setup & Acquisition | ✅ Complete | — |
| Phase 2: Core Processing | ✅ Complete | 209,462 |
| Phase 3: Safety Filter | ✅ Complete | — |
| Phase 4: API & Integration | ✅ Complete | — |
| Phase 5: Distribution | ⏳ Pending | — |
| Phase 6: Quick-Win Optimizations | ⏳ Pending | — |

**Current Status**: Core dictionary generated with 209K entries. 701 tests passing. Architecture and optimization docs written. Ready for distribution and performance tuning.
