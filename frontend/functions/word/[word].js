// GET /word/paani — server-rendered word detail page
import {
    escapeHtml,
    htmlHead,
    siteHeader,
    siteFooter,
    entryCard,
    htmlResponse,
    getDb,
} from '../_utils.js';

export async function onRequest(context) {
    const { params, env } = context;
    const slug = params.word || '';
    const db = getDb(env);

    if (!slug.trim()) {
        return htmlResponse(notFound(), 404);
    }

    // Look up by roman or hindi
    const entry = db.prepare(`
        SELECT * FROM entries
        WHERE word_hinglish_roman = ? OR word_hindi = ?
        LIMIT 1
    `).bind(slug, slug).first();

    if (!entry) {
        // Try partial match
        const partial = db.prepare(`
            SELECT * FROM entries
            WHERE word_hinglish_roman LIKE ? OR word_hindi LIKE ?
            LIMIT 1
        `).bind(`%${slug}%`, `%${slug}%`).first();

        if (partial) {
            const correctSlug = partial.word_hinglish_roman || encodeURIComponent(partial.word_hindi);
            return new Response(null, {
                status: 301,
                headers: { Location: `/word/${correctSlug}` },
            });
        }

        return htmlResponse(notFound(slug), 404);
    }

    const html = buildWordPage(entry, db);
    return htmlResponse(html);
}

function buildWordPage(entry, db) {
    const hindi = entry.word_hindi || '';
    const roman = entry.word_hinglish_roman || '';
    const def = entry.definition || '';
    const title = `${hindi} (${roman}) — ${def.substring(0, 80)}`;

    let page = htmlHead(title, `${hindi} (${roman}) — ${def}`);

    page += siteHeader();

    page += `<main class="container word-page">`;
    page += entryCard(entry, true);
    page += `</main>`;

    page += siteFooter();
    return page;
}

function notFound(slug) {
    const s = escapeHtml(slug || '');
    return `${htmlHead('Not Found', 'Word not found')}
${siteHeader()}
<main class="container not-found">
  <h1>Word not found</h1>
  ${s ? `<p>No entry found for <strong>${s}</strong>.</p>` : '<p>No word specified.</p>'}
  <p>Try <a href="/">searching</a> instead.</p>
</main>
${siteFooter()}`;
}
