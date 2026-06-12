-- D1 schema for HinglishKosh
-- Deploy: wrangler d1 execute hinglishkosh --file=frontend/src/schema/d1.sql

CREATE TABLE IF NOT EXISTS entries (
    id TEXT PRIMARY KEY,
    word_hindi TEXT NOT NULL,
    word_hinglish_roman TEXT NOT NULL DEFAULT '',
    definition TEXT NOT NULL DEFAULT '',
    part_of_speech TEXT NOT NULL DEFAULT '',
    example_sentence TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    confidence_score REAL NOT NULL DEFAULT 0,
    severity_score REAL NOT NULL DEFAULT 0,
    toxicity_flags TEXT NOT NULL DEFAULT '',
    synonyms TEXT NOT NULL DEFAULT '',
    antonyms TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '',
    head_word TEXT NOT NULL DEFAULT ''
);

CREATE INDEX idx_entries_hindi ON entries(word_hindi);
CREATE INDEX idx_entries_roman ON entries(word_hinglish_roman);

CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
    word_hindi,
    word_hinglish_roman,
    definition,
    example_sentence,
    content='entries',
    content_rowid='rowid',
    tokenize='unicode61'
);

-- Triggers to keep FTS in sync with entries table
CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
    INSERT INTO entries_fts(rowid, word_hindi, word_hinglish_roman, definition, example_sentence)
    VALUES (new.rowid, new.word_hindi, new.word_hinglish_roman, new.definition, new.example_sentence);
END;

CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
    INSERT INTO entries_fts(entries_fts, rowid, word_hindi, word_hinglish_roman, definition, example_sentence)
    VALUES ('delete', old.rowid, old.word_hindi, old.word_hinglish_roman, old.definition, old.example_sentence);
END;

CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
    INSERT INTO entries_fts(entries_fts, rowid, word_hindi, word_hinglish_roman, definition, example_sentence)
    VALUES ('delete', old.rowid, old.word_hindi, old.word_hinglish_roman, old.definition, old.example_sentence);
    INSERT INTO entries_fts(rowid, word_hindi, word_hinglish_roman, definition, example_sentence)
    VALUES (new.rowid, new.word_hindi, new.word_hinglish_roman, new.definition, new.example_sentence);
END;

CREATE TABLE IF NOT EXISTS related_words (
    entry_id TEXT NOT NULL,
    related_entry_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK(relation_type IN ('same_synset', 'broader', 'narrower')),
    PRIMARY KEY (entry_id, related_entry_id, relation_type)
);

CREATE INDEX idx_related_entry ON related_words(entry_id);
CREATE INDEX idx_related_related ON related_words(related_entry_id);
