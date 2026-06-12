// Shared utilities for HinglishKosh Pages Functions

const SAFE_THRESHOLD = 0.5;

/**
 * Escape HTML to prevent XSS in server-rendered pages
 */
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

/**
 * Build HTML head fragment shared across pages
 */
function htmlHead(title, description) {
    return `<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${escapeHtml(title)} — HinglishKosh</title>
<meta name="description" content="${escapeHtml(description)}">
<link rel="stylesheet" href="/style.css">
</head>
<body>`;
}

/**
 * Site header with search bar
 */
function siteHeader(activeQuery) {
    const q = escapeHtml(activeQuery || '');
    return `<header class="site-header">
  <div class="container">
    <a href="/" class="logo">हिंग्लिशकोश</a>
    <nav>
      <a href="/">Home</a>
      <a href="/about">About</a>
    </nav>
  </div>
  <div class="search-bar container">
    <form action="/search" method="get" role="search" id="search-form">
      <input
        type="search"
        name="q"
        id="search-input"
        value="${q}"
        placeholder="Search HinglishKosh... (e.g., paani, chai, नमस्ते)"
        autocomplete="off"
        aria-label="Search the dictionary"
      >
      <button type="submit">Search</button>
    </form>
    <div id="suggestions" class="suggestions" hidden></div>
  </div>
</header>`;
}

/**
 * Site footer
 */
function siteFooter() {
    return `<footer class="site-footer">
  <div class="container">
    <p>HinglishKosh (हिंग्लिशकोश) — <a href="https://github.com/apauldev/HinglishKosh">Open source</a> Hinglish-English dictionary. Licensed under GPL v3.</p>
  </div>
</footer>
</body>
</html>`;
}

/**
 * Render a single entry card (used in search results and word pages)
 */
function entryCard(entry, showFull) {
    const hindi = escapeHtml(entry.word_hindi || '');
    const roman = escapeHtml(entry.word_hinglish_roman || '');
    const def = escapeHtml(entry.definition || '');
    const pos = escapeHtml(entry.part_of_speech || '');
    const source = escapeHtml(entry.source || '');
    const example = escapeHtml(entry.example_sentence || '');
    const severity = entry.severity_score || 0;
    const isToxic = severity >= SAFE_THRESHOLD;

    let html = `<div class="entry-card${isToxic ? ' entry-toxic' : ''}">
  <div class="entry-head">`;

    if (showFull) {
        html += `<h1 class="entry-hindi">${hindi}</h1>
    <p class="entry-roman">${roman}</p>`;
    } else {
        html += `<a href="/word/${roman || encodeURIComponent(hindi)}" class="entry-link">
      <span class="entry-hindi">${hindi}</span>
      <span class="entry-roman">${roman}</span>
    </a>`;
    }

    html += `</div>
  <div class="entry-body">
    <p class="entry-def">${def}</p>
    <p class="entry-meta">${pos ? `<span class="pos">${pos}</span>` : ''} <span class="source">${source}</span></p>`;

    if (example && showFull) {
        html += `<blockquote class="entry-example">${example}</blockquote>`;
    }

    if (isToxic) {
        html += `<p class="toxicity-warning">⚠ Content warning: flagged (severity: ${severity.toFixed(2)})</p>`;
    }

    html += `</div>`;

    // Related words (only on full word page)
    if (showFull) {
        const relations = {
            same_synset: entry.same_synset || [],
            broader_terms: entry.broader_terms || [],
            narrower_terms: entry.narrower_terms || [],
        };
        const labels = {
            same_synset: 'Same synset',
            broader_terms: 'Broader terms',
            narrower_terms: 'Narrower terms',
        };

        for (const [key, items] of Object.entries(relations)) {
            if (items.length > 0) {
                html += `<div class="related-group">
          <h3>${labels[key]}</h3>
          <p>`;
                const links = items.map(r =>
                    `<a href="/word/${escapeHtml(r.word_hinglish_roman || encodeURIComponent(r.word_hindi))}" class="related-word">${escapeHtml(r.word_hindi)} (${escapeHtml(r.word_hinglish_roman)})</a>`
                );
                html += links.join(', ');
                html += `</p></div>`;
            }
        }
    }

    html += `</div>`;
    return html;
}

/**
 * JSON response helper
 */
function jsonResponse(data, status = 200) {
    return new Response(JSON.stringify(data), {
        status,
        headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'public, max-age=60, s-maxage=300',
        },
    });
}

/**
 * HTML response helper
 */
function htmlResponse(html, status = 200) {
    return new Response(html, {
        status,
        headers: {
            'Content-Type': 'text/html; charset=utf-8',
            'Cache-Control': 'public, max-age=60, s-maxage=300',
        },
    });
}

/**
 * Get database from environment
 */
function getDb(env) {
    return env.DB;
}

export {
    escapeHtml,
    htmlHead,
    siteHeader,
    siteFooter,
    entryCard,
    jsonResponse,
    htmlResponse,
    getDb,
    SAFE_THRESHOLD,
};
