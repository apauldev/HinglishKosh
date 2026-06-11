# Hinglish Dictionary — Implementation Plan

> A task-based, sequential blueprint for building a 100K+ entry Hinglish-English dictionary.

---

## Phase 1: Project Setup & Data Acquisition

### Task 1.1: Initialize Project Skeleton
- [ ] Create `pyproject.toml` with dependencies (`pandas`, `sqlite3`, `fastapi`, `uvicorn`, `requests`, `tqdm`)
- [ ] Create `src/__init__.py` and subpackage `__init__.py` files
- [ ] Create `data/raw/`, `data/processed/`, `data/output/` directories
- [ ] Create `.gitignore` for Python/data artifacts
- [ ] Add `README.md` with project overview

### Task 1.2: Download Hindi WordNet (IIT Bombay)
- [ ] Scrape or download Hindi WordNet JSON/XML from IIT Bombay's IndoWordNet portal
- [ ] Store raw files in `data/raw/wordnet/`
- [ ] Write `src/ingestion/wordnet_loader.py` to parse synsets, glosses, examples, POS tags
- [ ] Validate: count unique headwords, verify Hindi + English gloss pairs exist

### Task 1.3: Download Wiktionary Data (kaikki.org)
- [ ] Download `kaikki.org dictionaries/Hindi (hi).jsonl.gz` from kaikki.org
- [ ] Decompress and store in `data/raw/wiktionary/`
- [ ] Write `src/ingestion/wiktionary_loader.py` to parse JSONL entries
- [ ] Extract: headword, POS, definitions, examples, etymology
- [ ] Filter out non-Hindi/non-Urdu entries (keep only Devanagari script + common Roman forms)

### Task 1.4: Download Transliteration Models
- [ ] Download GoVarnam or IndicTrans transliteration model
- [ ] Store in `data/raw/translit/`
- [ ] Write `src/processing/transliterate.py` wrapper module

### Task 1.5: Download Supplemental Hinglish Datasets
- [ ] Download CoMuMDR dataset (if available)
- [ ] Download `eval_hinglish_top_v2` from Kaggle
- [ ] Store in `data/raw/supplemental/`
- [ ] Write `src/ingestion/supplemental_loader.py`

---

## Phase 2: Core Dictionary Processing

### Task 2.1: Build WordNet Core Dictionary
- [ ] Load parsed WordNet data into pandas DataFrame
- [ ] Create core entries with fields:
  - `word_hindi`, `word_hinglish_roman`, `definition`, `part_of_speech`
  - `example_sentence`, `synsets` (list of Princeton + IndoWordNet synset IDs)
  - `source`, `confidence_score` (1.0 for WordNet)
- [ ] Deduplicate by `word_hindi` + `definition_hash`
- [ ] Output: `data/processed/wordnet_core.json`

### Task 2.2: Build Wiktionary Extended Dictionary
- [ ] Load parsed Wiktionary data into DataFrame
- [ ] Normalize headwords (handle Unicode variations, ligatures)
- [ ] Resolve malformed entries (catch JSON parse errors, skip/repair)
- [ ] Create extended entries with same schema as core
- [ ] Assign `confidence_score` = 0.85 (lower than WordNet)
- [ ] Output: `data/processed/wiktionary_ext.json`

### Task 2.3: Merge & Deduplicate Dictionaries
- [ ] Load both processed dictionaries
- [ ] Use fuzzy matching (fuzzywuzzy/rapidfuzz) on romanized + Hindi headwords
- [ ] Priority: WordNet entries win on conflicts
- [ ] Merge definitions from both sources when non-overlapping
- [ ] Assign unified `id` (HIN-00001 format)
- [ ] Output: `data/processed/merged_dict.json`

### Task 2.4: Enhanced Definition Expansion (RAG)
- [ ] Identify entries with missing or Hindi-only definitions
- [ ] For each, retrieve existing Hindi definition + context (examples, synsets)
- [ ] Call LLM API to generate English definition supplement
- [ ] Store generated definitions with `source: "llm_generated"` and lower confidence (0.7)
- [ ] Manual validation: sample 100 entries, review accuracy
- [ ] Output: `data/processed/expanded_dict.json`

### Task 2.5: Generate Unified Dataset
- [ ] Assemble final dictionary with all fields from schema
- [ ] Add metadata block (version, total_entries, sources, license, date)
- [ ] Validate: all required fields present, no nulls in critical fields
- [ ] Output: `data/output/hinglish_dictionary_v1.json`

---

## Phase 3: Safety Filter (Optional)

### Task 3.1: Build Profanity Wordlist
- [ ] Compile Hindi/Hinglish profanity list from research papers
- [ ] Extract from `bekindprofanityfilter` package dictionary
- [ ] Supplement from Wikipedia Hindustani profanity page
- [ ] Include spelling variations (Devanagari, Roman, leet-speak)
- [ ] Store as `data/raw/profanity/master_list.json` with severity levels

### Task 3.2: Set Up Toxicity Detection Pipeline
- [ ] Load `tsmaitry/indic-toxicity-detector` from Hugging Face
- [ ] Create `src/safety/toxicity_classifier.py` wrapper
- [ ] Set confidence threshold: 0.70
- [ ] Create `src/safety/dictionary_matcher.py` for wordlist-based detection
- [ ] Create `src/safety/severity_scorer.py` for multi-model consensus

### Task 3.3: Process Full Dataset Through Safety Filter
- [ ] Run dictionary-based detection on all headwords
- [ ] Run ML-based classifier on definitions + example sentences
- [ ] Combine results into `toxicity_flags` array per entry
- [ ] Compute `severity_score` (0.0–1.0)
- [ ] Output: `data/output/hinglish_dictionary_v1_safe.json` (filtered subset)
- [ ] Output: `data/output/hinglish_dictionary_v1_flagged.json` (full with flags)

### Task 3.4: Validate Safety Filter
- [ ] Manual audit: 1,000 random entries
- [ ] Calculate false positive rate and false negative rate
- [ ] Tune thresholds, add whitelist for false positives
- [ ] Document known limitations

---

## Phase 4: API & Integration

### Task 4.1: Build REST API
- [ ] Create `src/api/main.py` with FastAPI
- [ ] Endpoints:
  - `GET /lookup?word={word}&safe=true`
  - `GET /search?q={query}&limit=20`
  - `GET /stats` (dataset metadata)
- [ ] Implement phonetic matching (soundex/metaphone for Roman spelling)
- [ ] Add CORS, rate limiting, health check

### Task 4.2: Generate Keyboard Formats
- [ ] Create `src/integration/aosp_dict_export.py`
- [ ] Convert dictionary to AOSP `.dict` format for OpenBoard/HeliBoard
- [ ] Generate SQLite FTS virtual table for offline app search
- [ ] Output: `data/output/hinglish.dict`, `data/output/hinglish.db`

### Task 4.3: Package & Publish
- [ ] Finalize `pyproject.toml` with entry points
- [ ] Add CLI tool: `hinglish-dict lookup <word>`
- [ ] Write tests in `tests/`
- [ ] Create GitHub Actions CI pipeline
- [ ] Prepare Hugging Face Dataset card
- [ ] Tag release: `v1.0.0`

---

## File Structure

```
hinglish-dict/
├── PLAN.md
├── README.md
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
│   │   └── rag_expand.py
│   ├── safety/
│   │   ├── __init__.py
│   │   ├── profanity_list.py
│   │   ├── toxicity_classifier.py
│   │   └── severity_scorer.py
│   ├── api/
│   │   └── main.py
│   └── integration/
│       ├── __init__.py
│       ├── aosp_dict_export.py
│       └── sqlite_export.py
├── tests/
│   ├── test_wordnet_loader.py
│   ├── test_wiktionary_loader.py
│   ├── test_merge.py
│   └── test_api.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── output/
├── scripts/
│   └── download_data.sh
└── .github/
    └── workflows/
        └── ci.yml
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

## Timeline Estimate

| Phase | Tasks | Estimated Time |
|---|---|---|
| Phase 1: Setup & Acquisition | 1.1–1.5 | 2–3 days |
| Phase 2: Core Processing | 2.1–2.5 | 5–7 days |
| Phase 3: Safety Filter | 3.1–3.4 | 3–4 days |
| Phase 4: API & Integration | 4.1–4.3 | 3–4 days |
| **Total** | | **13–18 days** |
