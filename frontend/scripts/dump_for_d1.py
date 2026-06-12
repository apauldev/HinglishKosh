"""Dump local SQLite DB to D1-compatible SQL with batched multi-value INSERTs."""
import sqlite3
import os

BATCH_SIZE = 10
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'hinglishkosh.db')
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', '.d1_dumps')
os.makedirs(OUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

def quote(v):
    if v is None:
        return "''"
    import re
    s = str(v).replace("'", "''")
    return f"'{s}'"

# ─── Entries ───
print("Dumping entries...")
cursor = conn.execute("SELECT * FROM entries ORDER BY id")
out = open(os.path.join(OUT_DIR, 'entries.sql'), 'w')
rows = []
count = 0
for row in cursor:
    rows.append(f"({quote(row['id'])},{quote(row['word_hindi'])},{quote(row['word_hinglish_roman'])},{quote(row['definition'])},{quote(row['part_of_speech'])},{quote(row['example_sentence'])},{quote(row['source'])},{row['confidence_score']},{row['severity_score']},{quote(row['toxicity_flags'])},{quote(row['synonyms'])},{quote(row['antonyms'])},{quote(row['tags'])},{quote(row['head_word'])},{quote(row['definition_en'])},{quote(row['definition_hinglish'])})")
    count += 1
    if len(rows) >= BATCH_SIZE:
        out.write("INSERT INTO entries(id,word_hindi,word_hinglish_roman,definition,part_of_speech,example_sentence,source,confidence_score,severity_score,toxicity_flags,synonyms,antonyms,tags,head_word,definition_en,definition_hinglish) VALUES\n" + ",\n".join(rows) + ";\n")
        rows = []
        print(f"  {count} entries...")
if rows:
    out.write("INSERT INTO entries(id,word_hindi,word_hinglish_roman,definition,part_of_speech,example_sentence,source,confidence_score,severity_score,toxicity_flags,synonyms,antonyms,tags,head_word,definition_en,definition_hinglish) VALUES\n" + ",\n".join(rows) + ";\n")
out.close()
print(f"  Done: {count} entries")

# ─── Related words ───
print("Dumping related_words...")
cursor = conn.execute("SELECT * FROM related_words ORDER BY entry_id, related_entry_id")
out = open(os.path.join(OUT_DIR, 'related_words.sql'), 'w')
rows = []
count = 0
for row in cursor:
    rows.append(f"({quote(row['entry_id'])},{quote(row['related_entry_id'])},{quote(row['relation_type'])})")
    count += 1
    if len(rows) >= BATCH_SIZE:
        out.write("INSERT INTO related_words(entry_id,related_entry_id,relation_type) VALUES\n" + ",\n".join(rows) + ";\n")
        rows = []
        print(f"  {count} related_words...")
if rows:
    out.write("INSERT INTO related_words(entry_id,related_entry_id,relation_type) VALUES\n" + ",\n".join(rows) + ";\n")
out.close()
print(f"  Done: {count} related_words")

conn.close()
print(f"\nSQL files written to {OUT_DIR}/")
