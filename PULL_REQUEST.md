## Description

Resolve all ruff linting errors and verify tests + pipeline still pass.

### Changes

| Category | Files | Description |
|---|---|---|
| **Duplicate keys** | `transliterate.py`, `test_1000_words.py` | Removed 340 duplicate keys from `_COMMON_WORDS` dict and 60 from `COMMON_WORDS_1000` |
| **Unused imports** | 6 test files | Removed unused `json`, `sqlite3`, `Path`, `pytest`, `_definition_hash`, `tempfile` imports |
| **Line length (E501)** | `pipeline.py`, `cli.py`, `supplemental_loader.py`, `wordnet_loader.py`, `toxicity_classifier.py` | Broke long lines under 100 chars |
| **Unused variables (F841)** | `pipeline.py` | Removed unused `linkage` and `all_entries` assignments |
| **Type annotations (UP045)** | `test_wiktionary_loader.py` | Changed `Optional[list]` → `list \| None` |

### Verification

```
✅ 701 tests passed, 6 skipped, 2 warnings
✅ Pipeline generated 209,462 entries successfully
✅ 0 ruff errors remaining
```

### No Functional Changes

This PR only cleans up code style — no behavior changes.
