// GET /api/suggest?q=cha&limit=8
// Lightweight autocomplete — returns just word_hindi + word_hinglish_roman
import { jsonResponse, getDb } from '../_utils.js';

export async function onRequest(context) {
    const { request, env } = context;
    const url = new URL(request.url);
    const q = url.searchParams.get('q') || '';
    const limit = Math.min(parseInt(url.searchParams.get('limit') || '8', 10), 20);

    if (!q.trim() || q.trim().length < 1) {
        return jsonResponse({ suggestions: [] });
    }

    const db = getDb(env);
    const query = q.trim();

    // Try exact prefix match on roman first, then hindi
    const results = db.prepare(`
        SELECT word_hindi, word_hinglish_roman
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
        LIMIT ?
    `).bind(
        `${query}%`, `${query}%`,
        query, query,
        `${query}%`,
        limit
    ).all();

    return jsonResponse({
        query: q,
        suggestions: results.results || [],
    });
}
