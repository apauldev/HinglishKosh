# HinglishKosh (हिंग्लिशकोश)

A comprehensive, open-source Hinglish-English dictionary dataset for keyboards, apps, and NLP research.

## Why?

Hinglish — the natural blend of Hindi and English — is how millions communicate daily, yet no open dictionary exists for it. HinglishKosh fills that gap: **100,000+ entries** sourced from WordNet, Wiktionary, and curated datasets, structured for integration into open-source keyboards like OpenBoard, HeliBoard, and FUTO Keyboard.

## What's Inside

| Component | Description |
|---|---|
| **Full Dataset** | Complete dictionary with definitions, examples, POS tags, and synset linkages |
| **Safe Dataset** | Filtered variant with profanity and toxic content flagged/removed |
| **REST API** | FastAPI server with phonetic search and safe-mode toggle |
| **Keyboard Formats** | Pre-built `.dict` files for AOSP-based keyboards |
| **CLI Tool** | `hinglish-dict lookup <word>` for quick lookups |

## Dataset Schema

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
```

## Architecture

```
Data Sources          Processing           Output
─────────────         ──────────           ──────
Hindi WordNet    ──►  Parse & Normalize ──► Full Dataset (JSON/CSV)
Wiktionary       ──►  Merge & Dedup    ──► Safe Dataset (filtered)
Supplemental     ──►  RAG Expand       ──► Keyboard (.dict)
Profanity Lists  ──►  Toxicity Filter  ──► SQLite FTS DB
                                         REST API
```

## Data Sources

| Source | License | Contribution |
|---|---|---|
| Hindi WordNet (IIT Bombay) | GPL 3.0 | Core curated entries |
| IndoWordNet-English Linked | Apache-compatible | Synset linkages |
| Wiktionary (kaikki.org) | CC BY-SA | Extended coverage |
| GoVarnam / IndicTrans | AGPL 3.0 / GPL | Transliteration |

## License

GPL 3.0 — compatible with all upstream data sources. See [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Whether it's new words, bug fixes, or integration help — open a PR or issue.

---

**HinglishKosh** — *हिंग्लिशकोश* — because Hinglish deserves a dictionary too.
