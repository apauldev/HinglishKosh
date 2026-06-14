CREATE TABLE entries (
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
    head_word TEXT NOT NULL DEFAULT '',
    definition_en TEXT NOT NULL DEFAULT '',
    definition_hinglish TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_entries_hindi ON entries(word_hindi);
CREATE INDEX idx_entries_roman ON entries(word_hinglish_roman);
CREATE TABLE related_words (
    entry_id TEXT NOT NULL,
    related_entry_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK(relation_type IN ('same_synset', 'broader', 'narrower')),
    PRIMARY KEY (entry_id, related_entry_id, relation_type)
);
CREATE INDEX idx_related_entry ON related_words(entry_id);
CREATE INDEX idx_related_related ON related_words(related_entry_id);
