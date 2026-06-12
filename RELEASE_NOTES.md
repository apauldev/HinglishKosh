## HinglishKosh v1.0.2

### Dataset

| Metric | Value |
|--------|-------|
| Total entries | 209,462 |
| Safe entries | 209,372 |
| WordNet | 153,204 |
| Wiktionary | 56,258 |
| Top POS | noun (138,067), verb (30,494), adjective (25,326), adj (6,568), name (3,755) |

### Files

| File | Description |
|------|-------------|
| `hinglish_dictionary_v1.json` | Full dataset (pretty-printed) |
| `hinglish_dictionary_v1.min.json` | Full dataset (compact) |
| `hinglish_dictionary_v1_safe.json` | Safe dataset (toxic filtered) |
| `hinglish_dictionary_v1_safe.min.json` | Safe dataset (compact) |
| `SHA256SUMS.txt` | File checksums |

### Usage

```bash
# CLI
pip install hinglish-dictionary
hinglish-dict lookup namaste

# API
uvicorn src.api.main:app --reload

# Python
import json
with open("hinglish_dictionary_v1.json") as f:
    data = json.load(f)
```

### Changes

- #6 #6
- #5 #5

**Full Changelog**: https://github.com/apauldev/HinglishKosh/compare/v1.0.1...v1.0.2