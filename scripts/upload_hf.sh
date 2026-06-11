#!/usr/bin/env bash
set -euo pipefail

# Upload dictionary dataset to Hugging Face Datasets.
# Usage: bash scripts/upload_hf.sh [dataset_name]
#
# Prerequisites: huggingface-cli authenticated (huggingface-cli login)
# Install: pip install huggingface_hub datasets

HF_DATASET="${1:-apauldev/HinglishKosh}"
OUTPUT_DIR="data/output"
JSON_FILE="$OUTPUT_DIR/hinglish_dictionary_v1.json"

echo "=== Upload to Hugging Face: $HF_DATASET ==="

# Check file exists
if [ ! -f "$JSON_FILE" ]; then
    echo "ERROR: $JSON_FILE not found. Run pipeline first."
    exit 1
fi

# Check huggingface-cli
if ! command -v huggingface-cli &> /dev/null; then
    echo "Installing huggingface_hub..."
    pip install huggingface_hub datasets
fi

# Create dataset card
cat > "$OUTPUT_DIR/README.md" << 'CARD'
---
language:
  - hi
  - en
  - hinglish
tags:
  - dictionary
  - multilingual
  - hindi
  - transliteration
  - nlp
task_categories:
  - text-retrieval
  - translation
license: gpl-3.0
pretty_name: HinglishKosh (हिंग्लिशकोश)
---

# HinglishKosh (हिंग्लिशकोश)

A comprehensive Hinglish-English dictionary dataset with 200K+ entries for keyboards, apps, and NLP research.

## Dataset Structure

Each entry contains:

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique identifier (HIN-XXXXX) |
| `word_hindi` | string | Devanagari headword |
| `word_hinglish_roman` | string | ISO 15919 romanization |
| `definition` | string | English definition |
| `part_of_speech` | string | POS tag (noun, verb, adj, etc.) |
| `example_sentence` | string | Example in Hindi |
| `source` | string | Data source (WordNet/Wiktionary) |
| `confidence_score` | float | 0.0-1.0 quality score |

## Usage

```python
import json

with open("hinglish_dictionary_v1.json") as f:
    data = json.load(f)

# Look up a word
for entry in data["dictionary"]:
    if entry["word_hindi"] == "पानी":
        print(f"{entry['word_hindi']} = {entry['definition']}")
        # पानी = water
```

## Sources

- **WordNet**: Hindi WordNet from IIT Bombay (40K+ synsets)
- **Wiktionary**: Hindi entries from kaikki.org (35K+ words)

## License

GPL-3.0 (compatible with all upstream data sources).
CARD

# Upload using huggingface-cli
echo "Uploading to Hugging Face..."
huggingface-cli upload \
    --repo-type dataset \
    "$HF_DATASET" \
    "$OUTPUT_DIR/" \
    --include "hinglish_dictionary_v1.json,hinglish_dictionary_v1.min.json,README.md"

echo ""
echo "Uploaded to: https://huggingface.co/datasets/$HF_DATASET"
