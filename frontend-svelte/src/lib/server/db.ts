import type { D1Database } from '@cloudflare/workers-types';
import type {
  Entry,
  RelatedWord,
  Suggestion,
  SearchResult,
  SuggestResult,
  LookupResult,
  Stats,
  SearchParams,
  SuggestParams,
  LookupParams,
} from './types';

const SAFE_THRESHOLD = 0.5;

function sanitizeQuery(query: string): string {
  return query
    .replace(/[^\w\s]/g, '')
    .trim()
    .split(/\s+/)
    .map((t) => `${t}*`)
    .join(' ');
}

export async function searchEntries(db: D1Database, params: SearchParams): Promise<SearchResult> {
  const { q, safe = false, limit = 20 } = params;
  const sanitized = q.trim();

  if (!sanitized) {
    return { query: q, count: 0, results: [] };
  }

  const query = sanitizeQuery(sanitized);
  const actualLimit = Math.min(limit, 100);

  try {
    const results = await db
      .prepare(
        `SELECT e.*, rank
         FROM entries_fts f
         JOIN entries e ON e.rowid = f.rowid
         WHERE entries_fts MATCH ?
         ORDER BY rank
         LIMIT ?`
      )
      .bind(query, actualLimit)
      .all<Entry>();

    let entries = results.results || [];

    if (safe) {
      entries = entries.filter((e) => (e.severity_score || 0) < SAFE_THRESHOLD);
    }

    return {
      query: q,
      count: entries.length,
      results: entries,
    };
  } catch {
    const like = `%${sanitized}%`;
    const fallback = await db
      .prepare(
        `SELECT * FROM entries
         WHERE word_hindi LIKE ? OR word_hinglish_roman LIKE ? OR definition LIKE ?
         LIMIT ?`
      )
      .bind(like, like, like, actualLimit)
      .all<Entry>();

    let entries = fallback.results || [];

    if (safe) {
      entries = entries.filter((e) => (e.severity_score || 0) < SAFE_THRESHOLD);
    }

    return {
      query: q,
      count: entries.length,
      results: entries,
      fallback: true,
    };
  }
}

export async function getSuggestions(
  db: D1Database,
  params: SuggestParams
): Promise<SuggestResult> {
  const { q, limit = 8 } = params;
  const query = q.trim();

  if (!query) {
    return { query: q, suggestions: [] };
  }

  const actualLimit = Math.min(limit, 20);

  const results = await db
    .prepare(
      `SELECT word_hindi, word_hinglish_roman
       FROM entries
       WHERE word_hinglish_roman LIKE ? OR word_hindi LIKE ?
       GROUP BY word_hinglish_roman
       ORDER BY
         CASE
           WHEN word_hinglish_roman = ? THEN 0
           WHEN word_hindi = ? THEN 1
           WHEN word_hinglish_roman LIKE ? THEN 2
           ELSE 3
         END,
         LENGTH(word_hinglish_roman) ASC
       LIMIT ?`
    )
    .bind(`${query}%`, `${query}%`, query, query, `${query}%`, actualLimit)
    .all<Suggestion>();

  return {
    query: q,
    suggestions: results.results || [],
  };
}

export async function lookupWord(db: D1Database, params: LookupParams): Promise<LookupResult> {
  const { word, safe = false, limit = 10 } = params;
  const sanitized = word.trim();

  if (!sanitized) {
    return { query: word, count: 0, results: [] };
  }

  const actualLimit = Math.min(limit, 50);

  const exact = await db
    .prepare(
      `SELECT * FROM entries
       WHERE word_hindi = ? OR word_hinglish_roman = ?
       LIMIT ?`
    )
    .bind(sanitized, sanitized.toLowerCase(), actualLimit)
    .all<Entry>();

  let results = exact.results || [];

  if (results.length === 0) {
    const like = `%${sanitized}%`;
    const fuzzy = await db
      .prepare(
        `SELECT * FROM entries
         WHERE word_hindi LIKE ? OR word_hinglish_roman LIKE ?
         LIMIT ?`
      )
      .bind(like, like, actualLimit)
      .all<Entry>();
    results = fuzzy.results || [];
  }

  if (safe) {
    results = results.filter((e) => (e.severity_score || 0) < SAFE_THRESHOLD);
  }

  return {
    query: word,
    count: results.length,
    results,
  };
}

export async function findBestMatch(db: D1Database, slug: string): Promise<Entry | null> {
  const entry = await db
    .prepare(
      `SELECT * FROM entries
       WHERE word_hinglish_roman = ? OR word_hindi = ?
       LIMIT 1`
    )
    .bind(slug, slug)
    .first<Entry>();

  if (entry) return entry;

  const partial = await db
    .prepare(
      `SELECT * FROM entries
       WHERE word_hinglish_roman LIKE ? OR word_hindi LIKE ?
       LIMIT 1`
    )
    .bind(`%${slug}%`, `%${slug}%`)
    .first<Entry>();

  return partial;
}

export async function getRelatedWords(
  db: D1Database,
  entryId: string
): Promise<{ same_synset: RelatedWord[]; broader: RelatedWord[]; narrower: RelatedWord[] }> {
  const related: { same_synset: RelatedWord[]; broader: RelatedWord[]; narrower: RelatedWord[] } = {
    same_synset: [],
    broader: [],
    narrower: [],
  };

  for (const relType of ['same_synset', 'broader', 'narrower'] as const) {
    const rows = await db
      .prepare(
        `SELECT e.word_hindi, e.word_hinglish_roman, e.id
         FROM related_words r
         JOIN entries e ON e.id = r.related_entry_id
         WHERE r.entry_id = ? AND r.relation_type = ?
         ORDER BY e.word_hinglish_roman
         LIMIT 20`
      )
      .bind(entryId, relType)
      .all<RelatedWord>();
    related[relType] = rows.results || [];
  }

  return related;
}

export async function getStats(db: D1Database): Promise<Stats> {
  const total = await db
    .prepare('SELECT COUNT(*) as count FROM entries')
    .first<{ count: number }>();
  const safe = await db
    .prepare('SELECT COUNT(*) as count FROM entries WHERE severity_score < 0.5')
    .first<{ count: number }>();
  const toxic = await db
    .prepare('SELECT COUNT(*) as count FROM entries WHERE severity_score >= 0.5')
    .first<{ count: number }>();
  const relations = await db
    .prepare('SELECT COUNT(*) as count FROM related_words')
    .first<{ count: number }>();

  const sources = await db
    .prepare(
      `SELECT source, COUNT(*) as count
       FROM entries
       GROUP BY source
       ORDER BY count DESC`
    )
    .all<{ source: string; count: number }>();

  const posDist = await db
    .prepare(
      `SELECT part_of_speech, COUNT(*) as count
       FROM entries
       WHERE part_of_speech != ''
       GROUP BY part_of_speech
       ORDER BY count DESC
       LIMIT 15`
    )
    .all<{ part_of_speech: string; count: number }>();

  return {
    total_entries: total?.count || 0,
    safe_entries: safe?.count || 0,
    toxic_entries: toxic?.count || 0,
    total_relation_links: relations?.count || 0,
    sources: sources.results || [],
    pos_distribution: posDist.results || [],
  };
}
