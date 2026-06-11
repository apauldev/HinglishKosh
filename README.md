# Hinglish Dictionary

A comprehensive Hinglish-English dictionary dataset (100K+ entries) for open-source keyboards and apps.

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Download data sources
bash scripts/download_data.sh

# Run pipeline
python -m src.processing.pipeline
```

## Dataset Schema

Each entry contains:

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique identifier (HIN-XXXXX) |
| `word_hindi` | string | Devanagari headword |
| `word_hinglish_roman` | string | Romanized transliteration |
| `definition` | string | English definition |
| `part_of_speech` | string | POS tag |
| `example_sentence` | string | Example in Hindi + Roman |
| `synsets` | list | WordNet synset IDs |
| `source` | string | Data source |
| `confidence_score` | float | 0.0–1.0 quality score |
| `toxicity_flags` | list | Safety labels |
| `severity_score` | float | 0.0–1.0 toxicity severity |

## License

GPL 3.0 (compatible with WordNet and IndoWordNet sources).
