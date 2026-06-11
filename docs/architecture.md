# HinglishKosh (हिंग्लिशकोश) — Architecture

## 1. Problem Statement

Over 600 million people in India communicate daily in **Hinglish** — a code-mixed blend of Hindi and English written in the Roman script without diacritics. Despite this scale, no open-source, structured dictionary existed that maps Devanagari headwords to their informal romanized spellings (e.g., `चाय` → `chai`, not `cāy`). Existing resources use academic ISO 15919 transliteration with diacritics, which doesn't match how people actually type on phones and keyboards.

HinglishKosh fills this gap with a **209,462-entry** Hinglish–English dictionary sourced from Hindi WordNet (IIT Bombay) and Wiktionary, augmented with rule-based informal transliteration, safety filtering, and multiple export formats.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA PIPELINE                               │
│                                                                     │
│  ┌──────────┐   ┌──────────────┐   ┌──────────┐   ┌─────────────┐  │
│  │ Ingestion │──▶│ Processing   │──▶│ Safety   │──▶│ Export      │  │
│  │           │   │              │   │          │   │             │  │
│  │ WordNet   │   │ Trans-       │   │ Profanity│   │ JSON        │  │
│  │ Wiktionary│   │ literation   │   │ ML Toxic │   │ AOSP .dict  │  │
│  │ Supple-   │   │ Merge/Dedup  │   │ Severity │   │ SQLite FTS5 │  │
│  │ mental    │   │ ID Assign    │   │ Scoring  │   │ Word list   │  │
│  └──────────┘   └──────────────┘   └──────────┘   └─────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │      CONSUMPTION         │
              │                          │
              │  ┌─────┐  ┌─────┐       │
              │  │ CLI │  │ API │       │
              │  └─────┘  └─────┘       │
              │                          │
              │  ┌──────────────────┐    │
              │  │ Integrations     │    │
              │  │ (AOSP, SQLite)   │    │
              │  └──────────────────┘    │
              └─────────────────────────┘
```

The system is organized into four pipeline stages followed by consumption interfaces:

| Layer | Directory | Responsibility |
|---|---|---|
| Ingestion | `src/ingestion/` | Parse raw source formats into unified schema |
| Processing | `src/processing/` | Transliterate, merge, deduplicate, assign IDs |
| Safety | `src/safety/` | Profanity detection, ML toxicity, severity scoring |
| Export | `src/integration/` | Serialize to JSON, AOSP, SQLite FTS5 |
| API | `src/api/` | FastAPI REST server |
| CLI | `src/cli.py` | Command-line dictionary tool |

---

## 3. Data Pipeline (Detailed)

### 3.1 Stage 1: Ingestion

#### WordNet Loader (`src/ingestion/wordnet_loader.py`)

Reads synset TSV files from the IndoWordNet dataset (IIT Bombay). Each line has the format:

```
synset_id<TAB>word1,word2,...<TAB>gloss:"example1  /  example2"<TAB>pos
```

**Process:**
1. Find the synset directory (`data/raw/wordnet/synsets/all.hindi`)
2. Parse each line into `(synset_id, words[], gloss, examples[], pos)`
3. Expand multi-word synsets into individual entries (each word gets its own row)
4. Assign `confidence_score: 1.0` (highest authority source)

**Edge cases handled:**
- Malformed lines (fewer than 4 fields) are logged and skipped
- Invalid synset IDs are caught with ValueError
- Gloss-example separator `:"` handles the case where no examples exist
- Multiple extraction layouts supported (`synsets/` vs `iwn_data/synsets/`)
- Falls back to `all.*` files if `all.hindi` doesn't exist

**Normalized output schema:**
```python
{
    "id": "WN-12345",                    # Synset-based ID
    "word_hindi": "पानी",                 # Devanagari headword
    "word_hinglish_roman": "pani",        # Stub (replaced later)
    "definition": "water",                # Gloss text
    "part_of_speech": "n",               # Part of speech tag
    "example_sentence": "...",            # First example
    "all_examples": ["..."],              # All examples
    "synsets": ["iwn-12345"],            # Synset reference
    "head_word": "पानी",                  # Canonical synset headword
    "source": "WordNet",
    "confidence_score": 1.0,
    "toxicity_flags": [],
    "severity_score": 0.0
}
```

**English-Hindi Linkage:**
The `load_english_hindi_linkage()` function loads a separate TSV mapping Hindi synsets to English words:
```
english_offset<TAB>hindi_synset_id<TAB>english_word<TAB>hindi_word
```
This is currently loaded into memory but not yet integrated into the output schema.

#### Wiktionary Loader (`src/ingestion/wiktionary_loader.py`)

Reads the kaikki.org Hindi JSONL dump. Each line is a JSON object with fields `word`, `lang_code`, `pos`, `forms[]`, `senses[]`.

**Process:**
1. Filter entries by `lang_code == "hi"`
2. Skip redirects
3. For each sense within an entry, extract definition, examples, synonyms, antonyms
4. Extract romanization from the `forms[]` array (looks for `"romanization"` or `"roman"` tags)
5. Assign `confidence_score: 0.85` (secondary source)

**Edge cases handled:**
- Malformed JSON lines are counted and logged (capped at 5 warnings)
- Entries with no senses (definitions) are silently skipped
- Entries with no definition in any sense are skipped
- Romanization extraction falls back to any Latin-script form if no tagged romanization exists
- Raw glosses have parenthetical qualifiers stripped (e.g., `"(chemistry) water"` → `"water"`)
- Examples with translations are concatenated: `"text (translation)"`

**Normalized output schema:**
```python
{
    "id": "WK-पानी-n-0",                # word-POS-sense_index
    "word_hindi": "पानी",
    "word_hinglish_roman": "pani",       # Extracted or empty
    "definition": "water",
    "part_of_speech": "n",
    "example_sentence": "...",
    "all_examples": ["..."],
    "synsets": [],
    "tags": ["chemistry"],
    "synonyms": ["जल"],
    "antonyms": [],
    "source": "Wiktionary",
    "confidence_score": 0.85,
    "toxicity_flags": [],
    "severity_score": 0.0
}
```

#### Supplemental Loader (`src/ingestion/supplemental_loader.py`)

Loads additional datasets (CSV, JSON, JSONL) from `data/raw/supplemental/`. Supports flexible column name detection to handle varying schemas.

**Column detection order for CSV:**
- Hindi: `hindi` → `word_hindi` → `hindi_word` → `word`
- English: `english` → `definition` → `meaning` → `eng`
- Roman: `roman` → `hinglish` → `romanized` → `transliteration`
- POS: `pos` → `part_of_speech` → `type`

**Edge cases handled:**
- Files with unrecognized extensions are skipped with a log message
- JSONL format is auto-detected by attempting to parse the first line
- Entries missing both Hindi and English text are rejected
- Column names are normalized to lowercase for case-insensitive matching

**Normalized output:**
- `confidence_score: 0.7` (lower than WordNet/Wiktionary)
- Source tagged as `supplemental/{filename}` for traceability

### 3.2 Stage 2: Processing

#### Transliteration (`src/processing/transliterate.py`)

Converts Devanagari text to informal Hinglish romanization using a three-tier approach:

```
1. Common words lookup   → 600+ exception dictionary
2. ISO 15919 conversion  →  Strip diacritics, apply Hindi pronunciation rules
3. Rule-based fallback   →  Character-by-character Devanagari→Roman mapping
```

**Tier 1: Common words (`_COMMON_WORDS`)**
A dictionary of 600+ manually curated Devanagari→Hinglish mappings for well-known words where rules would produce incorrect results. Examples:
- `नमस्ते` → `namaste` (not `namaste`)
- `हाँ` → `haan` (not `hā̃`)
- `पानी` → `paani` (not `pani`)
- `चाय` → `chai` (not `cāy`)

**Tier 2: ISO 15919 → Hinglish (`iso_to_hinglish()`)**
Converts academic romanization (used by Wiktionary) to informal spellings. Applied entry-by-entry:

| Rule | Example |
|---|---|
| `ā` → `aa` | `cāy` → `caay` → `chai` |
| `ī` → `ee` | `pānī` → `paanee` → `paani` |
| `ū` → `oo` | `sūraj` → `sooraj` |
| `c` → `ch` | `cāy` → `chai` (palatal stop) |
| `v` → `w` (then fix exceptions) | `havā` → `hawa`; `dhanyavaad` kept |
| `ay` → `ai` (word-end) | `cāy` → `caay` → `chai` |
| Nasalized vowels | `hā̃` → `haan`, `nahī̃` → `nahi` |
| Trailing long vowels shortened | `paanee` → `paani`, `sooraj` kept |

**Tier 3: Rule-based (`transliterate_rule_based()`)**
Character-by-character mapping using `_DEVANAGARI_MAP` (70+ mappings) for consonants, vowels, matras, nukta variants, and numerals. Post-processing collapses repeated characters to max 2 and normalizes whitespace.

**Pluggable backends:** The `transliterate()` function accepts a `method` parameter (`rule_based`, `govarnam`, `indictrans`) with graceful fallback to the rule-based engine if imports fail.

#### Merge (`src/processing/merge.py`)

Combines WordNet and Wiktionary entries using a priority-based strategy:

```
1. All WordNet entries become the base (confidence: 1.0)
2. For each Wiktionary entry:
   a. Try exact Devanagari match → merge synsets/examples
   b. Try fuzzy match on Hindi text using rapidfuzz (threshold: 85%)
   c. Try fuzzy match on romanized text
   d. Combined score = max(hindi_score, roman_score, 0.7*hindi + 0.3*roman)
3. Wiktionary entries without any match are appended as extended coverage
```

**Merge rules when a match is found (WordNet wins):**
- WordNet definition is kept
- Wiktionary synsets are appended to WordNet's list (if not already present)
- Wiktionary examples are appended to WordNet's list (if not already present)
- If WordNet lacks an example sentence, the first Wiktionary example fills it

**Edge cases:**
- Definition hash matching catches cases where same word has identical definitions across sources
- Fuzzy matching handles orthographic variations (nukta, anusvara differences)

#### Deduplication (`src/processing/dedup.py`)

Runs within the merge step to remove redundant entries:

1. Group by normalized Hindi headword (NFKD normalized, nukta-stripped, virama-stripped)
2. Within each group, deduplicate by MD5 hash of normalized definition
3. On duplicate, merge sources (e.g., `"WordNet+Wiktionary"`), examples, synsets
4. Keep the highest confidence score

**Normalization rules for matching:**
- Hindi: NFKD Unicode normalization, nukta removal, trailing virama strip
- Roman: lowercase, non-alphanumeric stripped, whitespace collapsed

### 3.3 Stage 3: Safety Filter

#### ProfanityMatcher (`src/safety/profanity_list.py`)

Dictionary-based profanity detection with leet-speak normalization:

1. Normalize text: lowercase → apply character substitutions → strip non-alphanumeric
2. Check each word against the profanity wordlist (direct match)
3. If no direct match, check if any 3+ character profanity is a substring
4. Return all matches with severity and category

**Character variation map handles common substitutions:**
- Leet: `0→o`, `1→i`, `3→e`, `4→a`, `5→s`, `7→t`, `$→s`, `@→a`
- Devanagari-Roman: `aa→a`, `ee→e`, `oo→o` (collapses long vowels)

The built-in wordlist (`_BUILTIN_PROFANITY`) is deliberately a placeholder — real data loads from an external JSON file via `load_wordlist()`.

#### ToxicityClassifier (`src/safety/toxicity_classifier.py`)

ML-based contextual toxicity detection using Hugging Face:

1. Attempts to load `tsmaitry/indic-toxicity-detector` via `transformers.pipeline`
2. If model loads successfully, classifies text and extracts toxicity/hate/offensive scores
3. Falls back to a simple heuristic if model unavailable

**Heuristic fallback** checks for English toxic indicators: `"hate"`, `"kill"`, `"die"`, `"stupid"`, `"idiot"` — intentionally basic, not for production.

#### Severity Scorer (`src/safety/severity_scorer.py`)

Combines dictionary and ML signals into a unified score:

```
combined_score = dict_severity × 0.4 + ml_severity × 0.6
```

**Toxicity determination:**
- `is_toxic = True` if combined_score >= 0.5, **or** dict_severity >= 0.8, **or** ML flags toxic

**Output per entry:**
- `severity_score` (0.0–1.0): Combined severity
- `toxicity_flags`: List of flags from both sources (`profanity`, `hate_speech`, `contextual_toxicity`, etc.)
- `components`: Debug info showing individual scores from each source

### 3.4 Stage 4: Pipeline Orchestration (`src/processing/pipeline.py`)

The `run_pipeline()` function coordinates the full workflow:

```
1. Load WordNet entries       → wordnet_loader.load_wordnet()
2. Load Wiktionary entries    → wiktionary_loader.load_wiktionary()
3. Load supplemental entries  → supplemental_loader.load_supplemental()
4. Merge dictionaries         → merge_dictionaries(wordnet, wiktionary + supplemental)
5. Fill romanized forms       → _ensure_roman(entries)
6. Assign sequential IDs      → assign_ids(entries)  (HIN-00001 format)
7. Compute metadata           → sources, POS distribution
8. Write JSON (full + compact)
```

**Output files:**
- `data/output/hinglish_dictionary_v1.json` — Pretty-printed JSON (indent=2)
- `data/output/hinglish_dictionary_v1.min.json` — Compact JSON (no whitespace)

**ID format:** `HIN-XXXXX` (sequential, zero-padded to 5 digits).

---

## 4. Consumption Interfaces

### 4.1 REST API (`src/api/main.py`)

A FastAPI server with four endpoints:

| Endpoint | Parameters | Description |
|---|---|---|
| `GET /health` | None | Returns status and entry count |
| `GET /stats` | None | Returns metadata (version, sources, POS distribution) |
| `GET /lookup` | `word`, `safe?`, `limit?` | Exact + fuzzy lookup by Hindi or Roman headword |
| `GET /search` | `q`, `safe?`, `limit?` | Partial-match search across headwords and definitions |

**Search algorithm (`_fuzzy_search`):**
```
Exact Hindi match             → score 100
Exact Roman match             → score 95
Partial Hindi match           → score 80
Partial Roman match           → score 75
Match in definition           → score 50
Sorted descending by score    → top N results
```

**Safe mode:** When `safe=true`, entries with `severity_score >= 0.5` are excluded.

**CORS:** Wide open (`allow_origins=["*"]`) — suitable for local/keyboard use, not production.

**Startup:** Dictionary is loaded lazily from `data/output/hinglish_dictionary_v1.json` on first request (via `@app.on_event("startup")`).

### 4.2 CLI (`src/cli.py`)

Three subcommands via argparse:

```
hinglish-dict lookup <word>   [--safe] [--limit N]
hinglish-dict search <query>  [--safe] [--limit N]
hinglish-dict stats
```

**Lookup** finds exact matches first (Hindi or Roman), then falls back to substring matching. **Search** uses scoring similar to the API but in-process. Both support `--safe` filtering and configurable `--data-dir`.

### 4.3 Integration Exports

#### AOSP .dict (`src/integration/aosp_dict_export.py`)

Tab-separated format compatible with OpenBoard, HeliBoard, and FUTO Keyboard:

```
word<TAB>frequency<TAB>locale<TAB>shortcut<TAB>bigram<TAB>pos
```

- Frequency = `confidence_score × 1000` (int)
- Locale = `"hi"`
- Toxic entries (severity >= 0.5) are excluded

Also exports `words.txt` — a flat sorted wordlist of unique Roman headwords.

#### SQLite FTS5 (`src/integration/sqlite_export.py`)

Two-table schema:

```sql
-- Main data table
CREATE TABLE dictionary (
    id TEXT PRIMARY KEY,
    word_hindi TEXT,
    word_hinglish_roman TEXT,
    definition TEXT,
    part_of_speech TEXT,
    example_sentence TEXT,
    source TEXT,
    confidence_score REAL,
    toxicity_flags TEXT,    -- comma-separated
    severity_score REAL
);

-- Full-text search virtual table (FTS5)
CREATE VIRTUAL TABLE dictionary_fts USING fts5(
    word_hindi, word_hinglish_roman, definition, example_sentence,
    content='dictionary', content_rowid='rowid'
);
```

Supports FTS5 query syntax (prefix, phrase, boolean) with BM25 ranking via `ORDER BY rank`. Safe mode filtering via SQL WHERE clause on `severity_score`.

---

## 5. Data Schema (Unified Entry)

```python
{
    # Identity
    "id": "HIN-00001",                          # Assigned by pipeline
    "word_hindi": "पानी",                        # Devanagari
    "word_hinglish_roman": "paani",             # Informal romanization

    # Meaning
    "definition": "water",                       # English definition
    "part_of_speech": "n",                      # Part of speech tag
    "example_sentence": "पानी पियो",           # First example
    "all_examples": ["पानी पियो", "..."],       # All examples

    # Source & quality
    "source": "WordNet",                        # WordNet / Wiktionary / supplemental/{name}
    "confidence_score": 1.0,                    # 0.0–1.0

    # Relations
    "synsets": ["iwn-12345"],                   # Synset IDs
    "synonyms": [],                             # Wiktionary synonyms
    "antonyms": [],                             # Wiktionary antonyms
    "tags": [],                                 # Sense qualifier tags
    "head_word": "पानी",                        # Canonical synset headword

    # Safety
    "toxicity_flags": [],                       # List of flag strings
    "severity_score": 0.0                       # 0.0–1.0 combined score
}
```

---

## 6. Configuration & Dependencies

### Core dependencies (`pyproject.toml`)
| Package | Purpose |
|---|---|
| `pandas>=2.0` | In-memory data handling |
| `rapidfuzz>=3.0` | Fuzzy string matching for merge/dedup |
| `transformers>=4.30` + `torch>=2.0` | ML toxicity classifier |
| `fastapi>=0.100` + `uvicorn>=0.22` | REST API server |
| `requests>=2.28`, `tqdm>=4.64` | Download utilities |

### Development tools
| Tool | Purpose |
|---|---|
| `pytest>=7.0` | Test runner |
| `ruff>=0.1` | Linter + formatter (line length 100, target py39) |
| `mypy>=1.0` | Static type checking (`warn_return_any = true`) |

### Python version
Python 3.9+ with `from __future__ import annotations` for postponed evaluation.

---

## 7. Test Structure (701 tests)

| Test File | Scope | Count (approx) |
|---|---|---|
| `test_1000_words.py` | Common word romanization, no-diacritic checks, pattern validation | 588 |
| `test_lookup.py` | Hindi→English lookup, Hindi→roman verification, structure | Large |
| `test_api.py` | REST API endpoint tests | Integration |
| `test_transliterate.py` | Rule-based and ISO conversion unit tests | Unit |
| `test_merge.py` | Merge/dedup logic | Unit |
| `test_safety.py` | Profanity/toxicity/severity scoring | Unit |
| `test_wordnet_loader.py` | WordNet TSV parsing | Unit |
| `test_wiktionary_loader.py` | Wiktionary JSONL parsing | Unit |
| `test_supplemental_loader.py` | Supplemental CSV/JSON loading | Unit |
| `test_basic.py` | Project structure, importability | Smoke |

---

## 8. CI/CD Pipeline

**GitHub Actions** (`.github/workflows/ci.yml`):
- Trigger: push/PR to `main`
- Steps: lint (ruff) → download data → run pipeline → run all tests

**Release script** (`scripts/release.sh`):
- Creates GitHub release with dataset + SHA256 checksums

**Hugging Face upload** (`scripts/upload_hf.sh`):
- Uploads dataset to Hugging Face Datasets hub

---

## 9. Directory Layout

```
hinglish-dict/
├── data/
│   ├── raw/
│   │   ├── wordnet/           ← IndoWordNet TSV files
│   │   ├── wiktionary/        ← kaikki.org JSONL dump
│   │   └── supplemental/      ← Additional CSV/JSON datasets
│   └── output/                ← Generated dictionaries
│       ├── hinglish_dictionary_v1.json
│       ├── hinglish_dictionary_v1.min.json
│       ├── hinglish_dict_v1.dict    ← AOSP keyboard format
│       └── hinglish_dict_v1.db      ← SQLite FTS5
├── src/
│   ├── api/main.py            ← FastAPI server
│   ├── cli.py                 ← argparse CLI
│   ├── ingestion/
│   │   ├── wordnet_loader.py
│   │   ├── wiktionary_loader.py
│   │   └── supplemental_loader.py
│   ├── processing/
│   │   ├── pipeline.py        ← Main orchestrator
│   │   ├── transliterate.py   ← Devanagari→Roman conversion
│   │   ├── merge.py           ← Multi-source merge
│   │   └── dedup.py           ← Deduplication
│   ├── safety/
│   │   ├── profanity_list.py  ← Dictionary-based profanity
│   │   ├── toxicity_classifier.py  ← ML toxicity model
│   │   └── severity_scorer.py ← Combined scoring
│   └── integration/
│       ├── aosp_dict_export.py    ← Keyboard format
│       └── sqlite_export.py       ← FTS5 database
├── tests/                     ← 701 tests
├── scripts/                   ← Release & distribution
├── docs/                      ← Architecture docs
├── pyproject.toml
└── PLAN.md                    ← Task tracking
```
