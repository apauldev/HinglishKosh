# HinglishKosh

> A comprehensive, open-source Hinglish-English dictionary dataset for keyboards, apps, and NLP research.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-991%20passed-brightgreen)](tests/)
[![Dataset](https://img.shields.io/badge/dataset-209K%20entries-orange)](#dataset)

---

## Why HinglishKosh?

Hinglish — the natural blend of Hindi and English — is how **over 600 million people** communicate daily across India. Yet no open dictionary exists for it.

HinglishKosh fills that gap: **200,000+ entries** sourced from WordNet and Wiktionary, with informal Hinglish romanization (no diacritics) — exactly how Indians actually write on WhatsApp, social media, and keyboards.

## Features

- **209,462 entries** from WordNet (153K) and Wiktionary (56K)
- **Two dataset versions** — full (all entries) and safe (toxic entries filtered out)
- **Informal Hinglish romanization** — `chai` not `cāy`, `aag` not `āg`, `hawa` not `havā`
- **REST API** with phonetic search and safe-mode filtering
- **AOSP keyboard export** — ready for OpenBoard, HeliBoard, FUTO Keyboard
- **SQLite FTS5** for fast offline search
- **CLI tool** for quick lookups
- **Safety filter** — profanity detection and toxicity scoring
- **991 tests passing** — including 588 common word romanization tests

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
# → paani: water (noun)

# Search by romanization
hinglish-dict search chai
# → चाय (chai): tea

# Show dataset stats
hinglish-dict stats
# → Total entries: 209,462
```

### As a REST API

```bash
# Start the server
uvicorn src.api.main:app --reload

# Lookup endpoint
curl "http://localhost:8000/lookup?word=नमस्ते"
# → {"word_hindi": "नमस्ते", "word_hinglish_roman": "namaste", ...}

# Search endpoint
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
  "id": "WN-12345",
  "word_hindi": "पानी",
  "word_hinglish_roman": "paani",
  "definition": "water",
  "part_of_speech": "noun",
  "example_sentence": "पानी पिओ (paani piyo)",
  "all_examples": ["पानी पिओ"],
  "synsets": ["iwn-12345"],
  "head_word": "पानी",
  "source": "WordNet",
  "confidence_score": 1.0,
  "toxicity_flags": [],
  "severity_score": 0.0
}
```

### Key Fields

| Field | Description |
|---|---|
| `word_hindi` | Devanagari script form |
| `word_hinglish_roman` | Informal Hinglish romanization (no diacritics) |
| `definition` | English definition |
| `part_of_speech` | noun, verb, adjective, etc. |
| `source` | WordNet or Wiktionary |
| `confidence_score` | 1.0 (WordNet) or 0.85 (Wiktionary) |
| `toxicity_flags` | List of detected content flags |
| `severity_score` | 0.0 (safe) to 1.0 (toxic) |

### Dataset Versions

The pipeline generates two dataset versions:

| File | Description |
|---|---|
| `hinglish_dictionary_v1.json` | Full dataset — all 209,462 entries |
| `hinglish_dictionary_v1_safe.json` | Safe dataset — toxic entries filtered (`severity_score < 0.5`) |

Both versions include `.min.json` compact variants for production use.

Use the safe version for keyboard apps and public-facing tools. Use the full version for NLP research where completeness matters.

## Android Keyboard Integration

### Third-Party Keyboards

HinglishKosh exports AOSP `.dict` files compatible with open-source Android keyboards:

| Keyboard | Hinglish Support | Notes |
|---|---|---|
| [OpenBoard](https://github.com/openboard-team/openboard) | Via custom dictionary | Import `.dict` file in settings |
| [HeliBoard](https://github.com/Helium314/HeliBoard) | Via custom dictionary | Fork of OpenBoard, actively maintained |
| [FUTO Keyboard](https://github.com/futo-org/android-keyboard) | Native support | Privacy-focused, supports custom dictionaries |

**Setup (OpenBoard/HeliBoard):**
1. Download `hinglish.dict` from [Releases](https://github.com/apauldev/HinglishKosh/releases)
2. Open keyboard settings → Dictionary → Import
3. Select the `.dict` file
4. Hinglish words will appear in suggestions

### Planned: Hinglish+English Keyboard

**Problem:** Currently, Indian users switch between 2-3 keyboards — English for coding/work, Hindi/Hinglish for chatting. This is friction.

**Solution:** A single keyboard that handles:
- English typing (QWERTY)
- Hindi transliteration (type "namaste" → suggestions include "नमस्ते")
- Hinglish mode (type "chai" → suggests "चाय")
- Auto-detection based on context

This would be the first keyboard built specifically for how Indians actually type — mixing English and Hindi naturally, without switching apps.

**Status:** Planning phase. Contributions welcome for keyboard development.

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
├─────────────────┬─────────────────┬─────────────────────────┤
│   Parse &       │  Transliterate  │   Merge &               │
│   Normalize     │  (ISO → Hinglish)│   Deduplicate          │
└─────────────────┴─────────────────┴─────────────────────────┘
         │                 │                     │
         ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                     Safety Filter                           │
├─────────────────┬─────────────────┬─────────────────────────┤
│  Profanity      │   Toxicity      │   Severity              │
│  Detection      │   Classifier    │   Scorer                │
└─────────────────┴─────────────────┴─────────────────────────┘
         │                 │                     │
         ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                       Output                                │
├─────────────────┬─────────────────┬─────────────────────────┤
│  Full Dataset   │  AOSP .dict     │   REST API              │
│  (JSON/CSV)     │  (Keyboards)    │   SQLite FTS5           │
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
│   ├── processing/         # Pipeline, merge, transliteration
│   ├── safety/             # Profanity, toxicity, severity scoring
│   ├── api/                # FastAPI REST server
│   ├── integration/        # AOSP dict export, SQLite FTS5
│   └── cli.py              # Command-line interface
├── tests/                  # 991 tests (unit + integration)
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
python -m pytest tests/test_api.py -v                    # REST API
```

**Note:** Random quality checks are skipped rather than failed to avoid flaky CI due to random sampling.

### Transliteration Accuracy

The rule-based engine scores **72.4%** against a 500-word hand-curated benchmark (365/500 words match how Hindi speakers actually type). The remaining 135 words have known schwa‑deletion edge cases tracked as `xfail` — they'll become passing as `common_words.json` grows. The pipeline test (1,000 words with dictionary overlay) passes at near‑100%.

| Metric | Value |
|--------|-------|
| Engine accuracy (500-word benchmark) | 72.4% (365/500) |
| Pipeline accuracy (1,000-word test) | 99%+ (with common_words.json) |
| Anusvāra → m before labials | ✅ Fixed |
| v → w in function words | ✅ Via common_words.json |
| Mid-word schwa deletion | ✅ Unicode algorithm implemented |
| Known gaps remaining | 135 words (edge cases) |



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
2. Runs the full pipeline
3. Generates SHA256 checksums
4. Creates a GitHub Release with all 4 JSON variants

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
