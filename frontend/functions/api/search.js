// GET /api/search?q=chai&safe=true&limit=20
import { jsonResponse, getDb } from '../_utils.js';

export async function onRequest(context) {
    const { request, env } = context;
    const url = new URL(request.url);
    const q = url.searchParams.get('q') || '';
    const safe = url.searchParams.get('safe') === 'true';
    const limit = Math.min(parseInt(url.searchParams.get('limit') || '20', 10), 100);

    if (!q.trim()) {
        return jsonResponse({ error: 'Missing search query' }, 400);
    }

    const db = getDb(env);

    // FTS5 search with prefix matching
    const query = q.trim().replace(/[^\w\s]/g, '').split(/\s+/).map(t => t + '*').join(' ');

    try {
        const results = await db.prepare(`
            SELECT e.*, rank
            FROM entries_fts f
            JOIN entries e ON e.rowid = f.rowid
            WHERE entries_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        `).bind(query, limit).all();

        let entries = results.results || [];

        if (safe) {
            entries = entries.filter(e => (e.severity_score || 0) < 0.5);
        }

        return jsonResponse({
            query: q,
            count: entries.length,
            results: entries,
        });
    } catch (err) {
        // Fallback: LIKE search if FTS fails (e.g., on short queries)
        const like = `%${q.trim()}%`;
        const fallback = await db.prepare(`
            SELECT * FROM entries
            WHERE word_hindi LIKE ? OR word_hinglish_roman LIKE ? OR definition LIKE ?
            LIMIT ?
        `).bind(like, like, like, limit).all();

        let entries = fallback.results || [];

        if (safe) {
            entries = entries.filter(e => (e.severity_score || 0) < 0.5);
        }

        return jsonResponse({
            query: q,
            count: entries.length,
            results: entries,
            fallback: true,
        });
    }
}
