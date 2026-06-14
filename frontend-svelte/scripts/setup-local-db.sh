#!/bin/bash
# Setup local D1 database for development.
# This copies the pre-built database into Miniflare's state directory
# so that `wrangler pages dev` has data.

set -e

DB_DIR=".wrangler/state/v3/d1/miniflare-D1DatabaseObject"
SRC_DB="hinglishkosh-d1.db"

if [ ! -f "$SRC_DB" ]; then
  echo "Error: $SRC_DB not found. Run 'sqlite3 hinglishkosh.db < migrate-to-d1.sql' first."
  exit 1
fi

# Start wrangler briefly to create the state directory and D1 file
echo "Initializing Miniflare state..."
npx wrangler pages dev .svelte-kit/cloudflare --compatibility-flag=nodejs_compat --port 9999 &
WRANGLER_PID=$!
sleep 5
kill $WRANGLER_PID 2>/dev/null
wait $WRANGLER_PID 2>/dev/null
sleep 2

# Find the most recently created D1 database file (the one pages dev made)
LATEST_DB=$(ls -t "$DB_DIR"/*.sqlite 2>/dev/null | head -1)

if [ -z "$LATEST_DB" ]; then
  echo "Error: Could not find D1 database in $DB_DIR"
  exit 1
fi

DB_NAME=$(basename "$LATEST_DB" .sqlite)
echo "Found D1 database: $DB_NAME"

# Check if it already has data
EXISTING=$(sqlite3 "$LATEST_DB" "SELECT COUNT(*) FROM entries;" 2>/dev/null || echo "0")
if [ "$EXISTING" -gt 1000 ]; then
  echo "Database already has $EXISTING entries. Skipping seed."
  exit 0
fi

# Replace with our populated database
echo "Seeding database with entries..."
rm -f "$DB_DIR/$DB_NAME.sqlite" "$DB_DIR/$DB_NAME.sqlite-shm" "$DB_DIR/$DB_NAME.sqlite-wal"
cp "$SRC_DB" "$LATEST_DB"
cp "${LATEST_DB}-shm" "${LATEST_DB}-shm" 2>/dev/null || true
cp "${LATEST_DB}-wal" "${LATEST_DB}-wal" 2>/dev/null || true

FINAL_COUNT=$(sqlite3 "$LATEST_DB" "SELECT COUNT(*) FROM entries;")
echo "Done! Database seeded with $FINAL_COUNT entries."
echo "Run 'pnpm dev' to start the development server."
