# HinglishKosh

> A comprehensive, open-source Hinglish-English dictionary dataset for keyboards, apps, and NLP research.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-1087%20passed-brightgreen)](tests/)
[![Dataset](https://img.shields.io/badge/dataset-115K%20entries-orange)](#dataset)

---

## Why HinglishKosh?

Hinglish — the natural blend of Hindi and English — is how **over 600 million people** communicate daily across India. Yet no open dictionary exists for it.

HinglishKosh fills that gap: **114,867 deduplicated entries** (expanded from 209,462 raw entries) sourced from WordNet and Wiktionary, with informal Hinglish romanization (no diacritics) — exactly how Indians actually write on WhatsApp, social media, and keyboards.

## Features

- **114,867 deduplicated entries** (15,152 multi-source) from WordNet and Wiktionary
- **Hindi/English definition classification** — `definition_hi`, `definition_en`, and `definition_lang` per entry (17K+ entries have English definitions)
- **Computed confidence scores** — 0.30–1.00 range, based on source quality, romanization method, multi-source confirmation, and definition completeness (toxic entries floored to ≤ 0.30)
- **Two dataset versions** — full (all entries) and safe (toxic entries filtered out)
- **Informal Hinglish romanization** — `chai` not `cāy`, `aag` not `āg`, `hawa` not `havā`
- **Hash-indexed REST API** — O(1) exact lookups, substring search with confidence tiebreaking
- **SQLite FTS5** — 65ms startup CLI, full-text search, offline-capable
- **AOSP keyboard export** — ready for OpenBoard, HeliBoard, FUTO Keyboard
- **Safety filter** — profanity detection and toxicity scoring
- **1087 tests passing** — including 588 common word romanization tests

## Quick Start

```bash
# Install
pip install -e .

# Download data sources
bash scripts/download_data.sh

# Run the pipeline
python -m src.processing.pipeline

# Look up a word
hinglish-dict lookup namaste
hinglish-dict search chai
hinglish-dict stats
```

## Usage

### As a CLI Tool

```bash
# Lookup a word
hinglish-dict lookup पानी
# → पानी (paani)
#   POS: noun
#   Definition: water
#   Source: Wiktionary | Confidence: 0.9193

# Filter by minimum confidence
hinglish-dict lookup paani --min-confidence 0.7

# Search by romanization (uses SQLite FTS5, shows confidence)
hinglish-dict search chai
# → चाय (chai): tea  [conf: 0.9193]

# Show dataset stats
hinglish-dict stats
# → Total entries: 114,867
```

### As a REST API

```bash
# Start the server
uvicorn src.api.main:app --reload

# Lookup endpoint (O(1) hash index for exact match)
curl "http://localhost:8000/lookup?word=नमस्ते"
# → {"query":"नमस्ते","results":[{...}],"count":1}

# Lookup with confidence floor (only entries with confidence >= 0.7)
curl "http://localhost:8000/lookup?word=paani&min_confidence=0.7"

# Search endpoint (results ordered by match score, then confidence)
curl "http://localhost:8000/search?q=chai&limit=10"

# Stats endpoint
curl "http://localhost:8000/stats"
```

### As a Python Library

```python
import json

with open("data/output/hinglish_dictionary_v1.json") as f:
    data = json.load(f)

# Build a lookup index
index = {entry["word_hindi"]: entry for entry in data["dictionary"]}

# Look up a word
entry = index.get("पानी")
print(entry["word_hinglish_roman"])  # → paani
print(entry["definition"])          # → water
```

## Dataset Schema

Each entry in the dictionary follows this schema:

```json
{
  "id": "HIN-148322",
  "word_hindi": "पानी",
  "word_hinglish_roman": "paani",
  "definition": "पानी",
  "definition_hi": "पानी",
  "definition_en": "water",
  "definition_lang": "mixed",
  "definition_hinglish": "paani",
  "example_hinglish": "paani piyo",
  "part_of_speech": "noun",
  "example_sentence": "पानी पिओ",
  "all_examples": ["पानी पिओ"],
  "synsets": ["iwn-12345"],
  "head_word": "पानी",
  "source": "WordNet",
  "sources": ["WordNet", "Wiktionary"],
  "confidence_score": 0.7267,
  "toxicity_flags": [],
  "severity_score": 0.0,
  "profanity": false
}
```

### Key Fields

| Field | Description |
|---|---|---|
| `word_hindi` | Devanagari script form |
| `word_hinglish_roman` | Informal Hinglish romanization (no diacritics) |
| `definition` | Primary definition (Hindi or English) |
| `definition_hi` | Hindi definition (when classified) |
| `definition_en` | English definition (when available) |
| `definition_lang` | `hi`, `en`, or `mixed` |
| `definition_hinglish` | Romanized version of Hindi definition |
| `example_hinglish` | Romanized version of example sentence |
| `part_of_speech` | noun, verb, adjective, etc. |
| `source` | Primary source (WordNet or Wiktionary) |
| `sources` | All contributing sources (post-merge) |
| `confidence_score` | Computed quality score (0.30–1.00) — see Confidence Scoring |
| `toxicity_flags` | List of detected content flags |
| `severity_score` | 0.0 (safe) to 1.0 (toxic) |
| `profanity` | Boolean, whether entry matches profanity list |

### Dataset Versions

The pipeline generates the following output files:

| File | Description |
|---|---|
| `hinglish_dictionary_v1.json` | Full dataset — 114,867 entries |
| `hinglish_dictionary_v1_safe.json` | Safe dataset — toxic entries filtered (`severity_score < 0.5`) |
| `hinglish_dictionary_v1_excluded.json` | List of 47 entries excluded from safe mode |
| `hinglish_dictionary_v1.db` | SQLite FTS5 database for fast CLI/API lookups |
| `hinglish_dictionary_v1.min.json` | Compact variant of full dataset (no whitespace) |
| `hinglish_dictionary_v1_safe.min.json` | Compact variant of safe dataset |

Use the safe version or SQLite DB for keyboard apps and public-facing tools. Use the full JSON for NLP research where completeness matters. The `.min.json` variants are optimized for production and network transfer.

**Note:** `definition_hi` is populated on all entries (Hindi or mixed definitions). `definition_en` is available on 30,000+ entries (Wiktionary English definitions + mixed-definition entries after WordNet/Wiktionary merge).

## Confidence Scoring

Every entry is assigned a `confidence_score` (0.30–1.00) reflecting its quality. The score is multiplicative — a low value in any dimension pulls the whole score down.

**Formula:** `base × romanization_mult × source_boost × completeness_mult`

| Signal | Values | Rationale |
|---|---|---|
| **Source base** | WordNet 0.95, Wiktionary 0.85, supplemental 0.70 | WordNet is hand-curated; Wiktionary is crowd-sourced |
| **Romanization method** | common_word 1.0, ISO 0.92, rule-based 0.75 | Override from `common_words.json` is most reliable; rule engine has known gaps |
| **Multi-source boost** | +0.03 per additional source | Confirmation from independent datasets increases trust |
| **Completeness** | both defns 1.05, English defn 1.03, Hindi+example 1.02, else 1.0 | More complete entries are more useful |

**Toxicity override:** Entries with `severity_score >= 0.5` are floored to ≤ 0.30 regardless of other signals. The 47 currently-flagged toxic entries sit exactly at 0.30.

The resulting distribution spans 14 distinct confidence levels (up from 2 before scoring was implemented):

```
0.30:      47  (toxic entries, floored)
0.66:   4,365  (Wiktionary, rule-based, English-only)
0.67:  14,341  (Wiktionary, rule-based, both defns)
0.69:  10,752  (Wiktionary, rule-based, Hindi + example)
0.73:  80,811  (WordNet, rule-based, Hindi + example)
0.77:   3,802  (WordNet, multi-source)
0.92:     393  (Wiktionary, ISO romanization, multi-source)
1.00:     186  (WordNet, common-word romanization, both defns, multi-source)
```

Use `--min-confidence` in the CLI or `min_confidence` in the API to filter low-confidence entries.

## Error Audit

The pipeline ships with an audit tool that measures where the dictionary makes mistakes, across four independent dimensions:

| Audit | What it checks |
|---|---|
| **Transliteration** | Benchmarks the rule-based engine against a 500-word hand-curated set, classifies failures by type (length mismatch, v/w, schwa handling, etc.) |
| **Merge quality** | Counts merged entries via the `sources` list, measures Hindi/English definition completeness, flags thin definitions |
| **Safety filter** | Finds profanity false negatives in definitions/examples, suggests missing wordlist entries |
| **Confidence faithfulness** | Verifies that confidence scores actually correlate with quality signals (def length, source, example coverage) |

```bash
# Run all audits
python -m src.quality.audit

# Run specific audits
python -m src.quality.audit --audit transliteration,merge

# Skip detailed examples for faster runs
python -m src.quality.audit --suppress-examples
```

Sample output (against the current dataset):

```
─── Audit 1: Transliteration Accuracy ───
  Benchmark (500 words): 379/500 = 75.8%
  Failures by type:
    length_mismatch: 85
    other_consonant: 14
    extra_chars: 8

─── Audit 2: Merge Quality ───
  Merged entries: 15,152 (13.2% of total)
  Definition completeness: hi=100.0%, en=100.0%, both=100.0%

─── Audit 4: Confidence Faithfulness ───
  0.30:      47 entries (toxic, floored)
  0.73:  80,811 entries (WordNet, rule-based)
  ...
```

The transliteration accuracy number (75.8%) is the headline metric — the remaining 24.2% are tracked as `xfail` and improve as `common_words.json` grows.

## Android Keyboard Integration

HinglishKosh exports AOSP `.dict` files that work with open-source Android keyboards. The dictionary provides romanized Hinglish word suggestions (e.g., typing "paa" suggests "paani") when your keyboard is in Hindi script mode.

### Download

Get `hinglish.dict` from the latest [GitHub Release](https://github.com/apauldev/HinglishKosh/releases).

### OpenBoard

1. Open **OpenBoard Settings** → **Dictionary** → **Import custom dictionary**
2. Select the downloaded `hinglish.dict` file
3. Switch to a Hindi keyboard layout — Hinglish words appear as suggestions

### HeliBoard

1. Open **HeliBoard Settings** → **Dictionary** → **Import dictionary**
2. Select `hinglish.dict`
3. Enable the Hindi keyboard in HeliBoard settings if not already active
4. Words are ranked by frequency (based on confidence scores)

### FUTO Keyboard

1. Open **FUTO Keyboard Settings** → **Dictionaries** → **Add custom dictionary**
2. Select `hinglish.dict`
3. The dictionary enriches FUTO's suggestion engine with 114K+ Hinglish words

### What to expect

After importing, words like these become available as you type:

| Type this... | See suggestions |
|-------------|----------------|
| `nam` | namaste, namaskar, namkeen |
| `paa` | paani, paanch, paagal |
| `cha` | chai, chaand, chakkar |
| `py` | pyaar, pyasa, pyaaz |

### Dataset Versions

The `.dict` file uses the **safe** dataset (toxic entries filtered out, severity_score < 0.5).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Data Sources                          │
├─────────────────┬─────────────────┬─────────────────────────┤
│  Hindi WordNet  │   Wiktionary    │    Supplemental         │
│  (IIT Bombay)   │  (kaikki.org)   │    (Custom lists)       │
└────────┬────────┴────────┬────────┴────────────┬────────────┘
         │                 │                     │
         ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Processing Pipeline                       │
├──────────────────────┬──────────────────────────────────────┤
│  Parse & Normalize   │  Transliterate (ISO → Hinglish)     │
├──────────────────────┼──────────────────────────────────────┤
│  Merge Dictionaries  │  Deduplicate by roman (merge data)  │
├──────────────────────┼──────────────────────────────────────┤
│  Classify Defns      │  Compute Confidence                  │
│  (hi/en/mixed)       │  (source × roman × completeness)    │
└────────┬─────────────┴──────────────────────┬───────────────┘
         │                                     │
         ▼                                     ▼
┌─────────────────────────────────────────────────────────────┐
│                     Safety Filter                           │
├─────────────────┬─────────────────┬─────────────────────────┤
│  Profanity      │   Toxicity      │   Severity              │
│  Detection      │   Classifier    │   Scorer                │
└─────────────────┴─────────────────┴─────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                       Output                                │
├─────────────────┬─────────────────┬─────────────────────────┤
│  Full Dataset   │  AOSP .dict     │   REST API              │
│  (JSON/SQLite)  │  (Keyboards)    │   (hash-indexed)        │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## Data Sources

| Source | License | Entries | Description |
|---|---|---|---|
| [Hindi WordNet](https://www.cfilt.iitb.ac.in/wordnet/) | GPL 3.0 | 153,204 | Core curated entries with synset linkages |
| [Wiktionary](https://kaikki.org) | CC BY-SA 4.0 | 56,258 | Extended coverage with etymologies |
| IndoWordNet-English | Apache 2.0 | — | Synset linkage mapping |

### Transliteration

The pipeline converts ISO 15919 romanization to informal Hinglish:

| ISO 15919 | Hinglish | Notes |
|---|---|---|
| `cāy` | `chai` | `c` → `ch`, `ā` → `a` |
| `āg` | `aag` | Long vowel preserved |
| `havā` | `hawa` | `v` → `w` |
| `pānī` | `paani` | Trailing `ī` → `i` |
| `dādā` | `dada` | Repeated vowels collapsed |

## Project Structure

```
hinglish-dict/
├── src/
│   ├── ingestion/          # Data loaders (WordNet, Wiktionary, Supplemental)
│   ├── processing/         # Pipeline, merge, transliteration, confidence scoring
│   ├── quality/            # Error audit tooling
│   ├── safety/             # Profanity, toxicity, severity scoring
│   ├── api/                # FastAPI REST server (hash-indexed)
│   ├── integration/        # AOSP dict export, SQLite FTS5
│   └── cli.py              # Command-line interface (SQLite-backed)
├── tests/                  # 1087 tests (unit + integration)
├── scripts/
│   ├── download_data.sh    # Download data sources
│   ├── release.sh          # Create GitHub release
│   └── upload_hf.sh        # Upload to Hugging Face
├── data/
│   ├── raw/                # Downloaded source data (gitignored)
│   ├── processed/          # Intermediate processing (gitignored)
│   └── output/             # Final dataset (gitignored, in releases)
├── PLAN.md                 # Implementation plan
├── pyproject.toml          # Python project config
└── README.md               # This file
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test suite
python -m pytest tests/test_word_transliterations.py -v  # Word romanization
python -m pytest tests/test_def_transliterations.py -v   # Definition transliteration
python -m pytest tests/test_lookup.py -v                 # Lookup accuracy
python -m pytest tests/test_api.py -v                    # REST API + export
python -m pytest tests/test_dedup_merge.py -v            # Dedup + merge logic
python -m pytest tests/test_confidence.py -v             # Confidence scoring
```

**Note:** Random quality checks are skipped rather than failed to avoid flaky CI due to random sampling.

### Transliteration Accuracy

The rule-based engine scores **75.8%** against a 500-word hand-curated benchmark (379/500 words match how Hindi speakers actually type). The remaining 121 words have known schwa‑deletion edge cases tracked as `xfail` — they'll become passing as `common_words.json` grows. The pipeline test (1,000 words with dictionary overlay) passes at near‑100%.

| Metric | Value |
|--------|-------|
| Engine accuracy (500-word benchmark) | 75.8% (379/500) |
| Pipeline accuracy (1,000-word test) | 99%+ (with common_words.json) |
| Anusvāra → m before labials | ✅ Fixed |
| v → w in function words | ✅ Via common_words.json |
| Mid-word schwa deletion | ✅ Unicode algorithm implemented |
| Known gaps remaining | 121 words (edge cases) |



## Contributing

Contributions welcome! Here's how:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Areas for Contribution

- Adding more entries from additional sources
- Improving romanization accuracy
- Expanding the safety filter
- Integration with more keyboard apps
- Documentation and examples

## Releasing

Releases are automated via GitHub Actions. When you push a `v*` tag, CI downloads data, runs the pipeline, and creates a GitHub Release with the dataset files.

```bash
# Install bump2version (one-time)
pip install bump2version

# Bump version (updates pyproject.toml + src/__init__.py, commits, tags)
bump2version patch   # 1.0.0 → 1.0.1 (bug fixes)
bump2version minor   # 1.0.0 → 1.1.0 (new features)
bump2version major   # 1.0.0 → 2.0.0 (breaking changes)

# Push commit + tag to trigger release
git push && git push --tags
```

The release workflow:
1. Downloads raw data sources (cached for speed)
2. Runs the full pipeline — generates JSON, SQLite FTS5, and AOSP `.dict`
3. Generates SHA256 checksums
4. Creates a GitHub Release with all dataset variants

## License

This project is licensed under the **GNU General Public License v3.0** — see the [LICENSE](LICENSE) file for details.

### Data Source Licenses

| Source | License | Compatibility |
|---|---|---|
| Hindi WordNet (IIT Bombay) | GPL 3.0 | ✅ Compatible |
| Wiktionary | CC BY-SA 4.0 | ✅ Compatible (GPLv3) |
| IndoWordNet-English | Apache 2.0 | ✅ Compatible |

## Acknowledgments

- [IIT Bombay](https://www.cfilt.iitb.ac.in/) for Hindi WordNet
- [Wiktionary contributors](https://kaikki.org) for the Hindi dictionary data
- The open-source keyboard community (OpenBoard, HeliBoard, FUTO)

---

**HinglishKosh** — *हिंग्लिशकोश* — because Hinglish deserves a dictionary too.
