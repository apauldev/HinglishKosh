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
    const slug = decodeURIComponent(params.word || '');
    const db = getDb(env);

    if (!slug.trim()) {
        return htmlResponse(notFound(), 404);
    }

    const entry = db.prepare(`
        SELECT * FROM entries
        WHERE word_hinglish_roman = ? OR word_hindi = ?
        LIMIT 1
    `).bind(slug, slug).first();

    if (!entry) {
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

    // Fetch related words from D1
    const related = {};
    for (const relType of ['same_synset', 'broader', 'narrower']) {
        const rows = db.prepare(`
            SELECT e.word_hindi, e.word_hinglish_roman, e.id
            FROM related_words r
            JOIN entries e ON e.id = r.related_entry_id
            WHERE r.entry_id = ? AND r.relation_type = ?
            ORDER BY e.word_hinglish_roman
            LIMIT 20
        `).bind(entry.id, relType).all();
        related[relType] = rows.results || [];
    }

    // Attach related words to entry for the template
    entry.same_synset = related.same_synset || [];
    entry.broader_terms = related.broader || [];
    entry.narrower_terms = related.narrower || [];

    const html = buildWordPage(entry);
    return htmlResponse(html);
}

function buildWordPage(entry) {
    const hindi = entry.word_hindi || '';
    const roman = entry.word_hinglish_roman || '';
    const def = entry.definition || '';
    const title = `${hindi} (${roman}) — ${def.substring(0, 80)}`;

    let page = htmlHead(title, `${hindi} (${roman}) — ${def}`);
    page += siteHeader();
    page += `<main class="max-w-4xl mx-auto px-margin-mobile md:px-margin-desktop py-12 min-h-screen">`;
    page += entryCard(entry, true);
    page += `</main>`;
    page += siteFooter();
    return page;
}

function notFound(slug) {
    const s = escapeHtml(slug || '');
    return `${htmlHead('Not Found', 'Word not found')}
${siteHeader()}
<main class="flex flex-1 items-center justify-center px-4">
  <div class="text-center">
    <p class="text-7xl font-bold text-indigo-600 dark:text-indigo-400">404</p>
    <h1 class="mt-4 text-2xl font-bold text-gray-900 dark:text-white">Word not found</h1>
    ${s ? `<p class="mt-2 text-gray-500 dark:text-gray-400">No entry found for <strong>${s}</strong>.</p>` : '<p class="mt-2 text-gray-500 dark:text-gray-400">No word specified.</p>'}
    <div class="mt-8 flex justify-center gap-4">
      <a href="/" class="rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-all hover:bg-indigo-500 active:scale-95">Go home</a>
      <a href="/search" class="rounded-xl border border-gray-200 bg-white px-6 py-3 text-sm font-semibold text-gray-700 shadow-sm transition-all hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700">Search</a>
    </div>
  </div>
</main>
${siteFooter()}`;
}
