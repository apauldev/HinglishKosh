// GET /api/stats
import { jsonResponse, getDb } from '../_utils.js';

export async function onRequest(context) {
    const { env } = context;
    const db = getDb(env);

    const total = db.prepare('SELECT COUNT(*) as count FROM entries').first();
    const safe = db.prepare('SELECT COUNT(*) as count FROM entries WHERE severity_score < 0.5').first();
    const toxic = db.prepare('SELECT COUNT(*) as count FROM entries WHERE severity_score >= 0.5').first();
    const relations = db.prepare('SELECT COUNT(*) as count FROM related_words').first();

    const sources = db.prepare(`
        SELECT source, COUNT(*) as count
        FROM entries
        GROUP BY source
        ORDER BY count DESC
    `).all();

    const posDist = db.prepare(`
        SELECT part_of_speech, COUNT(*) as count
        FROM entries
        WHERE part_of_speech != ''
        GROUP BY part_of_speech
        ORDER BY count DESC
        LIMIT 15
    `).all();

    return jsonResponse({
        total_entries: total.count,
        safe_entries: safe.count,
        toxic_entries: toxic.count,
        total_relation_links: relations.count,
        sources: sources.results || [],
        pos_distribution: posDist.results || [],
    });
}
