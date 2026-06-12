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
    const activePos = (url.searchParams.get('pos') || '').trim().toLowerCase();

    const db = getDb(env);

    let results = [];

    if (q.trim()) {
        const query = q.trim().replace(/[^\w\s]/g, '').split(/\s+/).map(t => t + '*').join(' ');

        try {
            const res = await db.prepare(`
                SELECT e.*, rank
                FROM entries_fts f
                JOIN entries e ON e.rowid = f.rowid
                WHERE entries_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            `).bind(query, limit).all();
            results = res.results || [];
        } catch (err) {
            const like = `%${q.trim()}%`;
            const res = await db.prepare(`
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

    // Compute unfiltered counts before filtering by POS
    const unfilteredCounts = {};
    for (const e of results) {
        const pos = e.part_of_speech || 'other';
        unfilteredCounts[pos] = (unfilteredCounts[pos] || 0) + 1;
    }

    if (activePos) {
        results = results.filter(e => (e.part_of_speech || '').toLowerCase() === activePos);
    }

    const html = buildSearchPage(q, results, activePos, unfilteredCounts);
    return htmlResponse(html);
}

function buildSearchPage(query, results, activePos, unfilteredCounts) {
    const title = query ? `"${query}" search results` : 'Search';
    let page = htmlHead(title, `Search results for "${query}" on HinglishKosh`);

    page += siteHeader(query);

    page += `<main class="max-w-container-max mx-auto px-margin-mobile md:px-margin-desktop py-stack-lg">`;

    if (!query) {
        page += `<div class="text-center py-16">
        <h1 class="font-headline-md text-headline-md text-on-surface dark:text-[#e6e1e5]">Search HinglishKosh</h1>
        <p class="font-body-lg text-body-lg text-on-surface-variant dark:text-[#cac4d0] mt-4">Type a word above to get started.</p>
      </div></main>`;
        page += siteFooter();
        return page;
    }

    // Build sidebar POS filter links (use unfiltered counts)
    const totalAll = Object.values(unfilteredCounts || {}).reduce((a, b) => a + b, 0);
    const total = results.length;
    const baseUrl = `/search?q=${encodeURIComponent(query)}`;

    let posFilters = '';
    const allCls = !activePos ? 'font-body-md text-body-md text-primary font-bold' : 'font-body-md text-body-md text-on-surface-variant';
    posFilters += `<li><a href="${escapeHtml(baseUrl)}" class="${allCls}">All Results (${totalAll})</a></li>`;
    for (const [posName, cnt] of Object.entries(unfilteredCounts || {}).sort()) {
        const escPos = escapeHtml(posName.charAt(0).toUpperCase() + posName.slice(1));
        const isActive = activePos === posName.toLowerCase();
        const cls = isActive ? 'font-body-md text-body-md text-primary font-bold' : 'font-body-md text-body-md text-on-surface-variant hover:text-primary transition-colors';
        const href = `${baseUrl}&pos=${encodeURIComponent(posName)}`;
        posFilters += `<li><a href="${escapeHtml(href)}" class="${cls}">${escPos} (${cnt})</a></li>`;
    }

    // Source counts (unfiltered)
    const srcCounts = {};
    for (const e of results) {
        const src = e.source || 'Other';
        srcCounts[src] = (srcCounts[src] || 0) + 1;
    }
    let srcFilters = '';
    for (const [srcName, cnt] of Object.entries(srcCounts).sort()) {
        srcFilters += `<li><span class="font-body-md text-body-md text-on-surface-variant dark:text-[#cac4d0]">${escapeHtml(srcName)} (${cnt})</span></li>`;
    }

    page += `<div class="grid grid-cols-1 md:grid-cols-12 gap-gutter">`;

    // Sidebar
    page += `<aside class="hidden md:block md:col-span-3 space-y-stack-lg">
      <section>
        <h3 class="font-label-caps text-label-caps text-on-surface-variant mb-4 dark:text-[#cac4d0]">PART OF SPEECH</h3>
        <ul class="space-y-2">${posFilters}</ul>
      </section>
      <section>
        <h3 class="font-label-caps text-label-caps text-on-surface-variant mb-4 dark:text-[#cac4d0]">SOURCE</h3>
        <ul class="space-y-2">${srcFilters}</ul>
      </section>
    </aside>`;

    // Results area
    page += `<div class="md:col-span-9">`;
    page += `<div class="mb-stack-lg border-b border-outline-variant pb-stack-md flex justify-between items-end dark:border-[#49454f]">
      <h2 class="font-headline-md text-headline-md text-on-surface dark:text-[#e6e1e5]">Results for &lsquo;${escapeHtml(query)}&rsquo; <span class="text-on-surface-variant font-normal opacity-70 dark:text-[#cac4d0]">(${total} match${total !== 1 ? 'es' : ''})</span></h2>
    </div>`;

    if (total === 0) {
        const escQ = escapeHtml(query);
        page += `<p class="font-body-lg text-body-lg text-on-surface-variant dark:text-[#cac4d0]">No results found for <strong class="text-on-surface dark:text-[#e6e1e5]">${escQ}</strong>. Try a different search term.</p>`;
    } else {
        page += `<div class="space-y-gutter">`;
        for (const entry of results) {
            page += entryCard(entry, false);
        }
        page += `</div>`;
    }

    page += `</div></div></main>`;
    page += siteFooter();
    return page;
}
