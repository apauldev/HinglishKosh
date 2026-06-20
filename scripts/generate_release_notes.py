#!/usr/bin/env python3
"""Generate release notes with dataset stats and PR changelog."""

import json
import subprocess
import sys
from pathlib import Path


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    output_file = Path("RELEASE_NOTES.md")

    data = json.load(open("data/output/hinglish_dictionary_v1.json"))
    meta = data.get("meta", {})
    entries = meta.get("total_entries", 0)
    safe = meta.get("safe_entries", 0)
    sources = meta.get("source_counts", {})
    pos = meta.get("pos_distribution", {})

    # Get tags and find last one
    tags = (
        subprocess.run(["git", "tag", "-l"], capture_output=True, text=True)
        .stdout.strip()
        .split("\n")
    )
    tags = [t for t in tags if t and t != f"v{version}"]
    last_tag = tags[-1] if tags else ""

    # Get merge commits (PRs) since last tag
    log_range = f"{last_tag}..HEAD" if last_tag else "HEAD"
    prs = subprocess.run(
        ["git", "log", "--oneline", "--merges", log_range],
        capture_output=True,
        text=True,
    ).stdout.strip()

    changes = []
    for line in prs.split("\n"):
        if "Merge pull request" in line:
            # Format: "Merge pull request #6 from user/branch"
            parts = line.split("#")
            if len(parts) > 1:
                pr_num = parts[1].split()[0]
                changes.append(f"- #{pr_num}")

    pos_top = sorted(pos.items(), key=lambda x: -x[1])[:5]
    pos_str = ", ".join(f"{p} ({c:,})" for p, c in pos_top)

    compare_url = (
        f"https://github.com/apauldev/HinglishKosh/compare/{last_tag}...v{version}"
        if last_tag
        else f"https://github.com/apauldev/HinglishKosh/tree/v{version}"
    )

    notes = f"""## HinglishKosh v{version}

### Dataset

| Metric | Value |
|--------|-------|
| Total entries | {entries:,} |
| Safe entries | {safe:,} |
| WordNet | {sources.get("WordNet", 0):,} |
| Wiktionary | {sources.get("Wiktionary", 0):,} |
| Top POS | {pos_str} |

### Files

| File | Description |
|------|-------------|
| `hinglish_dictionary_v1.json` | Full dataset (pretty-printed) |
| `hinglish_dictionary_v1.min.json` | Full dataset (compact) |
| `hinglish_dictionary_v1_safe.json` | Safe dataset (toxic filtered) |
| `hinglish_dictionary_v1_safe.min.json` | Safe dataset (compact) |
| `hinglish.dict` | Keyboard dictionary (OpenBoard/HeliBoard/FUTO) |
| `hinglish_words.txt` | Word list (one per line) |
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

{chr(10).join(changes) if changes else "- Initial release"}

**Full Changelog**: {compare_url}"""

    output_file.write_text(notes)
    print(f"Release notes written to {output_file}")


if __name__ == "__main__":
    main()
