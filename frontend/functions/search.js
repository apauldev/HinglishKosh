// GET /search?q=chai — server-rendered search results page
import {
    escapeHtml,
    htmlHead,
    siteHeader,
    siteFooter,
    entryCard,
    htmlResponse,
    getDb,
} from './_utils.js';

export async function onRequest(context) {
    const { request, env } = context;
    const url = new URL(request.url);
    const q = url.searchParams.get('q') || '';
    const safe = url.searchParams.get('safe') === 'true';
    const limit = Math.min(parseInt(url.searchParams.get('limit') || '20', 10), 100);

    const db = getDb(env);

    let results = [];
    let error = null;

    if (q.trim()) {
        const query = q.trim().replace(/[^\w\s]/g, '').split(/\s+/).map(t => t + '*').join(' ');

        try {
            const res = db.prepare(`
                SELECT e.*, rank
                FROM entries_fts f
                JOIN entries e ON e.rowid = f.rowid
                WHERE entries_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            `).bind(query, limit).all();

            results = res.results || [];
        } catch (err) {
            // Fallback for short queries that FTS can't handle
            const like = `%${q.trim()}%`;
            const res = db.prepare(`
                SELECT * FROM entries
                WHERE word_hindi LIKE ? OR word_hinglish_roman LIKE ? OR definition LIKE ?
                LIMIT ?
            `).bind(like, like, like, limit).all();
            results = res.results || [];
        }

        if (safe) {
            results = results.filter(e => (e.severity_score || 0) < 0.5);
        }
    }

    const html = buildSearchPage(q, results);
    return htmlResponse(html);
}

function buildSearchPage(query, results) {
    const title = query ? `"${query}" search results` : 'Search';
    let page = htmlHead(title, `Search results for "${query}" on HinglishKosh`);

    page += siteHeader(query);

    page += `<main class="container search-page">
  <h1>${escapeHtml(query) ? `Results for "${escapeHtml(query)}"` : 'Search'}</h1>`;

    if (results.length === 0) {
        page += `<p class="no-results">No results found${query ? ` for <strong>${escapeHtml(query)}</strong>` : ''}. Try a different search term.</p>`;
    } else {
        page += `<p class="result-count">${results.length} result${results.length !== 1 ? 's' : ''} found</p>
    <div class="results-list">`;
        for (const entry of results) {
            page += entryCard(entry, false);
        }
        page += `</div>`;
    }

    page += `</main>`;
    page += siteFooter();
    return page;
}
