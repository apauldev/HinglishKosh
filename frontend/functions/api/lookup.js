// GET /api/lookup?word=paani&safe=true&limit=10
import { jsonResponse, getDb } from '../_utils.js';

export async function onRequest(context) {
    const { request, env } = context;
    const url = new URL(request.url);
    const word = url.searchParams.get('word') || '';
    const safe = url.searchParams.get('safe') === 'true';
    const limit = Math.min(parseInt(url.searchParams.get('limit') || '10', 10), 50);

    if (!word.trim()) {
        return jsonResponse({ error: 'Missing word parameter' }, 400);
    }

    const db = getDb(env);

    // Exact match first
    const exact = db.prepare(`
        SELECT * FROM entries
        WHERE word_hindi = ? OR word_hinglish_roman = ?
        LIMIT ?
    `).bind(word, word.toLowerCase(), limit).all();

    let results = exact.results || [];

    // Fallback: fuzzy/LIKE search
    if (results.length === 0) {
        const like = `%${word}%`;
        const fuzzy = db.prepare(`
            SELECT * FROM entries
            WHERE word_hindi LIKE ? OR word_hinglish_roman LIKE ?
            LIMIT ?
        `).bind(like, like, limit).all();
        results = fuzzy.results || [];
    }

    // Filter safe if requested
    if (safe) {
        results = results.filter(e => (e.severity_score || 0) < 0.5);
    }

    return jsonResponse({
        query: word,
        count: results.length,
        results: results,
    });
}
