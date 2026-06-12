#!/usr/bin/env bash
# Deploy HinglishKosh to Cloudflare Pages + D1
#
# Prerequisites:
#   1. npm install -g wrangler
#   2. wrangler login
#   3. wrangler d1 create hinglishkosh
#   4. In Pages dashboard: Settings → Functions → D1 bindings → add "DB" → hinglishkosh
#   5. python -m src.processing.pipeline
#   6. python frontend/src/seed/enrich.py
#
# Usage:
#   CLOUDFLARE_D1_ID="uuid" ./frontend/src/seed/deploy.sh
#
# Secrets:
#   - CLOUDFLARE_API_TOKEN: set via `wrangler login` or env var (never committed)
#   - D1 database UUID: configure in Pages dashboard, or pass via CLOUDFLARE_D1_ID env var
#   - No secrets are written to files in this repo

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_DIR="$(cd "$FRONTEND_DIR/.." && pwd)"

echo "=== HinglishKosh Deploy ==="
echo ""

# Step 1: Verify dataset
ENRICHED_JSON="$PROJECT_DIR/data/output/hinglish_dictionary_v1.json"
if [ ! -f "$ENRICHED_JSON" ]; then
    echo "ERROR: Enriched dataset not found at $ENRICHED_JSON"
    echo "Run: python -m src.processing.pipeline && python frontend/src/seed/enrich.py"
    exit 1
fi
echo "✓ Dataset: $(python3 -c "import json; d=json.load(open('$ENRICHED_JSON')); print(f\"{d['meta']['total_entries']:,} entries\")")"

# Step 2: Verify D1 database exists
echo ""
echo "=== D1 Database ==="
DB_ID="${CLOUDFLARE_D1_ID:-}"
if [ -z "$DB_ID" ]; then
    echo "⚠  CLOUDFLARE_D1_ID not set."
    echo "   The D1 binding must be configured in the Cloudflare Pages Dashboard:"
    echo "   Dashboard → hinglishkosh → Settings → Functions → D1 Database Bindings"
    echo "   Variable name: DB   |   Database: hinglishkosh"
    echo ""
    echo "   To find your D1 ID: wrangler d1 list"
else
    echo "✓ D1 database ID provided"
fi

# Step 3: Apply schema (if DB_ID is set, do it now)
if [ -n "$DB_ID" ]; then
    echo ""
    echo "=== Schema ==="
    wrangler d1 execute hinglishkosh --file="$FRONTEND_DIR/src/schema/d1.sql" --remote
    echo "✓ Schema applied"
fi

# Step 4: Seed data
echo ""
echo "=== Seeding Data ==="
echo "Building local SQLite database..."
python3 "$FRONTEND_DIR/src/seed/seed.py" \
    --input "$ENRICHED_JSON" \
    --output "$FRONTEND_DIR/hinglishkosh.db" \
    --schema "$FRONTEND_DIR/src/schema/d1.sql"

if [ -n "$DB_ID" ]; then
    echo "Dumping data to SQL and importing to D1..."
    python3 -c "
import sqlite3
conn = sqlite3.connect('$FRONTEND_DIR/hinglishkosh.db')
conn.row_factory = sqlite3.Row

def esc(s):
    if s is None: return 'NULL'
    return \"'\" + str(s).replace(\"'\", \"''\") + \"'\"

with open('$FRONTEND_DIR/.seed_entries.sql', 'w') as f:
    total = conn.execute('SELECT COUNT(*) FROM entries').fetchone()[0]
    f.write(f'-- {total} entries\\n')
    offset = 0
    while True:
        batch = conn.execute(f'SELECT * FROM entries LIMIT 500 OFFSET {offset}').fetchall()
        if not batch: break
        for row in batch:
            f.write(f\"INSERT INTO entries VALUES ({esc(row['id'])}, {esc(row['word_hindi'])}, {esc(row['word_hinglish_roman'])}, {esc(row['definition'])}, {esc(row['part_of_speech'])}, {esc(row['example_sentence'])}, {esc(row['source'])}, {row['confidence_score']}, {row['severity_score']}, {esc(row['toxicity_flags'])}, {esc(row['synonyms'])}, {esc(row['antonyms'])}, {esc(row['tags'])}, {esc(row['head_word'])});\\n\")
        offset += 500
    f.write('\\n')

with open('$FRONTEND_DIR/.seed_related.sql', 'w') as f:
    for row in conn.execute('SELECT * FROM related_words'):
        f.write(f\"INSERT OR IGNORE INTO related_words VALUES ({esc(row['entry_id'])}, {esc(row['related_entry_id'])}, {esc(row['relation_type'])});\\n\")

conn.close()
" 2>&1 | tail -1

    wrangler d1 execute hinglishkosh --file="$FRONTEND_DIR/.seed_entries.sql" --remote --split
    echo "✓ Entries imported"

    wrangler d1 execute hinglishkosh --file="$FRONTEND_DIR/.seed_related.sql" --remote --split
    echo "✓ Related words imported"

    # Cleanup temp seed files
    rm -f "$FRONTEND_DIR/.seed_entries.sql" "$FRONTEND_DIR/.seed_related.sql"
fi

# Cleanup local DB
rm -f "$FRONTEND_DIR/hinglishkosh.db"

# Step 5: Deploy Pages
echo ""
echo "=== Deploy Pages ==="
cd "$FRONTEND_DIR"
wrangler pages deploy public --commit-dirty=true
echo "✓ Pages deployed"

echo ""
echo "=== Done ==="
echo "Site: https://hinglishkosh.pages.dev"
echo ""
echo "Next steps (in Cloudflare Dashboard):"
echo "  1. D1 binding: go to hinglishkosh → Settings → Functions → D1 Database Bindings"
echo "     Variable name: DB   |   Database: hinglishkosh"
echo "  2. Custom domain: hinglishkosh → Custom domains → Set up"
echo "  3. Rate limiting: Security → WAF → Rate limiting rules"
echo ""
echo "Secrets never written to committed files ✓"
