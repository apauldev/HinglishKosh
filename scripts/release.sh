#!/usr/bin/env bash
set -euo pipefail

# Release script — creates a GitHub release with the dictionary dataset.
# Usage: bash scripts/release.sh v1.0.0
#
# Prerequisites: gh CLI authenticated (gh auth login)

VERSION="${1:-v1.0.0}"
OUTPUT_DIR="data/output"
ASSETS=(
    "$OUTPUT_DIR/hinglish_dictionary_v1.json"
    "$OUTPUT_DIR/hinglish_dictionary_v1.min.json"
)

echo "=== HinglishKosh Release: $VERSION ==="

# Verify output files exist
for asset in "${ASSETS[@]}"; do
    if [ ! -f "$asset" ]; then
        echo "ERROR: $asset not found. Run pipeline first."
        exit 1
    fi
done

# Generate checksums
echo "Generating checksums..."
cd "$OUTPUT_DIR"
sha256sum hinglish_dictionary_v1.json hinglish_dictionary_v1.min.json > SHA256SUMS.txt
cd -
echo "Checksums:"
cat "$OUTPUT_DIR/SHA256SUMS.txt"

# Create GitHub release with assets
echo ""
echo "Creating GitHub release $VERSION..."
gh release create "$VERSION" \
    --title "HinglishKosh $VERSION" \
    --notes "## HinglishKosh (हिंग्लिशकोश) $VERSION

### Dataset Stats
- Total entries: $(python3 -c "import json; d=json.load(open('$OUTPUT_DIR/hinglish_dictionary_v1.json')); print(d['meta']['total_entries'])")
- Sources: WordNet (IIT Bombay), Wiktionary (kaikki.org)
- License: GPL-3.0

### Files
- \`hinglish_dictionary_v1.json\` — Full dataset (pretty-printed)
- \`hinglish_dictionary_v1.min.json\` — Compact dataset (production)
- \`SHA256SUMS.txt\` — File checksums

### Integration
- API: \`pip install hinglish-dictionary\`
- Keyboard: Import \`.dict\` files for OpenBoard/HeliBoard
- CLI: \`hinglish-dict lookup <word>\`" \
    "${ASSETS[@]}" \
    "$OUTPUT_DIR/SHA256SUMS.txt"

echo ""
echo "Release $VERSION created successfully!"
echo "View at: https://github.com/apauldev/HinglishKosh/releases/tag/$VERSION"
