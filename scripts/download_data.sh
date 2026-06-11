#!/usr/bin/env bash
set -euo pipefail

# Download all raw data sources for the HinglishKosh dictionary project.
# Usage: bash scripts/download_data.sh

RAW_DIR="data/raw"
mkdir -p "$RAW_DIR"/{wordnet,wiktionary,supplemental,profanity}

echo "=== 1/4 Downloading Hindi WordNet (IIT Bombay) ==="
WORDNET_DIR="$RAW_DIR/wordnet"
if [ ! -f "$WORDNET_DIR/iwn_data.tar.gz" ]; then
    echo "Downloading IndoWordNet data (~31 MB)..."
    wget -q --show-progress -O "$WORDNET_DIR/iwn_data.tar.gz" \
        "https://www.dropbox.com/s/t29eqq19nt5eygs/iwn_data.tar.gz?dl=1" || {
        echo "WARN: Dropbox download failed. Manual download needed:"
        echo "  https://www.dropbox.com/s/t29eqq19nt5eygs/iwn_data.tar.gz?dl=1"
        echo "  Extract to: $WORDNET_DIR/"
    }
fi
if [ -f "$WORDNET_DIR/iwn_data.tar.gz" ] && [ ! -d "$WORDNET_DIR/synsets" ]; then
    echo "Extracting WordNet data..."
    cd "$WORDNET_DIR" && tar xzf iwn_data.tar.gz 2>/dev/null || true
    cd -
fi

echo ""
echo "=== 2/4 Downloading Wiktionary Hindi (kaikki.org) ==="
WIK_DIR="$RAW_DIR/wiktionary"
if [ ! -f "$WIK_DIR/kaikki-hindi.jsonl" ]; then
    echo "Downloading Hindi Wiktionary data (~149 MB)..."
    wget -q --show-progress -O "$WIK_DIR/kaikki-hindi.jsonl" \
        "https://kaikki.org/dictionary/Hindi/kaikki.org-dictionary-Hindi.jsonl" || {
        echo "WARN: Download failed. Manual download needed:"
        echo "  https://kaikki.org/dictionary/Hindi/kaikki.org-dictionary-Hindi.jsonl"
    }
fi

echo ""
echo "=== 3/4 Downloading English-Hindi Synset Linkage ==="
LINKAGE_DIR="$RAW_DIR/wordnet"
if [ ! -f "$LINKAGE_DIR/english-hindi-linked.tsv" ]; then
    echo "Downloading IWN-En linkage data..."
    wget -q --show-progress -O "$LINKAGE_DIR/english-hindi-linked.tsv" \
        "https://raw.githubusercontent.com/cfiltnlp/IWN-En/main/data/english-hindi-linked.tsv" || {
        echo "WARN: Linkage download failed."
    }
fi

echo ""
echo "=== 4/4 Preparing Supplemental Datasets Directory ==="
mkdir -p "$RAW_DIR/supplemental"
echo "Place additional Hinglish datasets (CSV/JSON) in: $RAW_DIR/supplemental/"
echo "  - CoMuMDR dataset"
echo "  - eval_hinglish_top_v2 (Kaggle)"

echo ""
echo "=== Done ==="
echo ""
echo "Downloaded data:"
echo "  WordNet:     $RAW_DIR/wordnet/"
echo "  Wiktionary:  $RAW_DIR/wiktionary/"
echo "  Linkage:     $RAW_DIR/wordnet/english-hindi-linked.tsv"
echo "  Supplemental: $RAW_DIR/supplemental/"
