// Shared utilities for HinglishKosh Pages Functions

const SAFE_THRESHOLD = 0.5;

const TAILWIND_CONFIG = `tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "tertiary-fixed": "#e0e3e5",
        "surface-container-highest": "#d3e4fe",
        "inverse-surface": "#213145",
        "primary-fixed": "#e1e0ff",
        "primary-container": "#6063ee",
        "secondary-container": "#dae2fd",
        "on-secondary-container": "#5c647a",
        "surface-container-low": "#eff4ff",
        "on-error": "#ffffff",
        "on-background": "#0b1c30",
        "tertiary-fixed-dim": "#c4c7c9",
        "on-secondary": "#ffffff",
        "on-secondary-fixed": "#131b2e",
        "on-surface": "#0b1c30",
        "error-container": "#ffdad6",
        "surface-bright": "#f8f9ff",
        "on-tertiary-fixed-variant": "#444749",
        "surface": "#f8f9ff",
        "on-tertiary-fixed": "#191c1e",
        "surface-dim": "#cbdbf5",
        "on-tertiary-container": "#fbfdff",
        "surface-container-lowest": "#ffffff",
        "inverse-on-surface": "#eaf1ff",
        "inverse-primary": "#c0c1ff",
        "on-primary": "#ffffff",
        "outline": "#767586",
        "surface-container": "#e5eeff",
        "primary": "#4648d4",
        "secondary-fixed": "#dae2fd",
        "error": "#ba1a1a",
        "secondary-fixed-dim": "#bec6e0",
        "on-primary-fixed": "#07006c",
        "on-primary-fixed-variant": "#2f2ebe",
        "tertiary-container": "#727577",
        "background": "#f8f9ff",
        "on-surface-variant": "#464554",
        "surface-container-high": "#dce9ff",
        "surface-tint": "#494bd6",
        "primary-fixed-dim": "#c0c1ff",
        "outline-variant": "#c7c4d7",
        "on-tertiary": "#ffffff",
        "on-primary-container": "#fffbff",
        "on-secondary-fixed-variant": "#3f465c",
        "tertiary": "#595c5e",
        "surface-variant": "#d3e4fe",
        "secondary": "#565e74",
        "on-error-container": "#93000a"
      },
      borderRadius: { DEFAULT: "0.125rem", lg: "0.25rem", xl: "0.5rem", full: "0.75rem" },
      spacing: { "stack-lg": "32px", "stack-md": "12px", "stack-sm": "4px", gutter: "24px", "container-max": "1440px", "margin-desktop": "48px", "margin-mobile": "16px" },
      fontFamily: { "hindi-entry": ["Noto Sans Devanagari"], "display-word": ["Inter"], "definition-num": ["Inter"], "label-caps": ["Inter"], "display-word-mobile": ["Inter"], "body-md": ["Inter"], "headline-md": ["Inter"], "body-lg": ["Inter"] },
      fontSize: {
        "hindi-entry": ["42px", { lineHeight: "60px", fontWeight: "500" }],
        "display-word": ["48px", { lineHeight: "56px", letterSpacing: "-0.02em", fontWeight: "700" }],
        "definition-num": ["14px", { lineHeight: "20px", fontWeight: "700" }],
        "label-caps": ["12px", { lineHeight: "16px", letterSpacing: "0.05em", fontWeight: "600" }],
        "display-word-mobile": ["36px", { lineHeight: "40px", letterSpacing: "-0.02em", fontWeight: "700" }],
        "body-md": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "headline-md": ["24px", { lineHeight: "32px", fontWeight: "600" }],
        "body-lg": ["18px", { lineHeight: "28px", fontWeight: "400" }]
      }
    }
  }
}`;

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function htmlHead(title, description) {
    return `<!DOCTYPE html>
<html class="light" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>${escapeHtml(title)} — HinglishKosh</title>
<meta name="description" content="${escapeHtml(description || title)}"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Devanagari:wght@400;500;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script>${TAILWIND_CONFIG}</script>
<style>
.material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; vertical-align: middle; }
body { background-color: #f8fafc; }
.premium-card { background-color: #ffffff; border: 1px solid #e2e8f0; transition: box-shadow 0.2s ease-in-out; }
.premium-card:hover { box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05); }
</style>
<link rel="stylesheet" href="/style.css"/>
</head>
<body class="font-body-md text-on-surface bg-background antialiased selection:bg-primary-fixed-dim">`;
}

function siteHeader(activeQuery) {
    const q = escapeHtml(activeQuery || '');
    return `<header class="bg-surface dark:bg-on-background border-b border-outline-variant dark:border-on-surface-variant sticky top-0 z-50">
<div class="flex justify-between items-center w-full px-margin-mobile md:px-margin-desktop py-4 max-w-container-max mx-auto">
<div class="flex items-center gap-8">
<a class="flex items-center gap-2.5 group" href="/" aria-label="HinglishKosh home">
<svg viewBox="0 0 36 36" class="h-9 w-9 shrink-0">
<defs>
<linearGradient id="logo-g" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
<stop stop-color="#4648d4"/>
<stop offset="1" stop-color="#7c3aed"/>
</linearGradient>
</defs>
<rect width="36" height="36" rx="9" fill="url(#logo-g)"/>
<text x="18" y="24" text-anchor="middle" font-family="system-ui,-apple-system,sans-serif" font-weight="700" font-size="17" fill="white">हिं</text>
</svg>
<div class="flex flex-col leading-tight">
<span class="text-base font-bold tracking-tight text-on-surface dark:text-[#e6e1e5]">हिंग्लिशकोश</span>
<span class="text-[11px] font-medium tracking-wider text-on-surface-variant dark:text-[#cac4d0] uppercase">HinglishKosh</span>
</div>
</a>
<nav class="hidden md:flex gap-6">
<a class="text-primary dark:text-primary-fixed font-bold border-b-2 border-primary dark:border-primary-fixed pb-1 font-label-caps text-label-caps" href="/">Home</a>
<a class="text-on-surface-variant dark:text-outline-variant hover:text-primary-container dark:hover:text-primary-fixed-dim transition-colors font-label-caps text-label-caps" href="/about">About</a>
</nav>
</div>
<div class="flex-1 max-w-md mx-8 hidden md:block">
<form action="/search" method="get" role="search" class="relative">
<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">search</span>
<input id="search-input" class="w-full pl-10 pr-4 py-2 bg-surface-container-lowest border border-outline-variant rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none font-body-md text-body-md" name="q" value="${q}" placeholder="Search for a word..." type="text"/>
<div id="suggestions" class="suggestions" hidden></div>
</form>
</div>
<div class="flex items-center gap-4">
<button id="theme-toggle" class="text-on-surface-variant p-2 rounded-full hover:bg-surface-container-high transition-colors" aria-label="Toggle theme">
<span class="material-symbols-outlined">dark_mode</span>
</button>
</div>
</div>
</header>`;
}

function siteFooter() {
    return `<footer class="bg-surface-container-low dark:bg-on-background border-t border-outline-variant dark:border-on-surface-variant">
<div class="flex flex-col md:flex-row justify-between items-start md:items-center w-full px-margin-mobile md:px-margin-desktop py-stack-lg max-w-container-max mx-auto gap-8">
<div class="flex flex-col gap-4">
<div class="flex items-center gap-2.5">
<svg viewBox="0 0 36 36" class="h-9 w-9 shrink-0">
<rect width="36" height="36" rx="9" fill="url(#logo-g)"/>
<text x="18" y="24" text-anchor="middle" font-family="system-ui,-apple-system,sans-serif" font-weight="700" font-size="17" fill="white">हिं</text>
</svg>
<span class="font-display-word text-headline-md text-primary dark:text-primary-fixed">हिंग्लिशकोश</span>
</div>
<p class="text-on-secondary-container dark:text-secondary-fixed-dim max-w-sm font-body-md text-body-md">An open source Hinglish-English dictionary for how India actually types.</p>
<div class="text-on-secondary-container dark:text-secondary-fixed-dim font-label-caps text-label-caps mt-4">© <span id="cYear">2024</span> HinglishKosh · GPL v3</div>
</div>
<div class="grid grid-cols-2 gap-12 md:flex md:gap-16">
<div class="flex flex-col gap-3">
<span class="font-label-caps text-label-caps font-bold text-on-surface mb-2 dark:text-[#e6e1e5]">PROJECT</span>
<a class="font-body-md text-body-md text-on-secondary-container dark:text-secondary-fixed-dim hover:underline decoration-primary transition-all" href="/about">About</a>
<a class="font-body-md text-body-md text-on-secondary-container dark:text-secondary-fixed-dim hover:underline decoration-primary transition-all" href="https://github.com/apauldev/HinglishKosh">GitHub</a>
<a class="font-body-md text-body-md text-on-secondary-container dark:text-secondary-fixed-dim hover:underline decoration-primary transition-all" href="https://github.com/apauldev/HinglishKosh/blob/main/LICENSE">License</a>
</div>
<div class="flex flex-col gap-3">
<span class="font-label-caps text-label-caps font-bold text-on-surface mb-2 dark:text-[#e6e1e5]">COMMUNITY</span>
<a class="font-body-md text-body-md text-on-secondary-container dark:text-secondary-fixed-dim hover:underline decoration-primary transition-all" href="https://github.com/apauldev/HinglishKosh/issues">Feedback</a>
<a class="font-body-md text-body-md text-on-secondary-container dark:text-secondary-fixed-dim hover:underline decoration-primary transition-all" href="https://github.com/apauldev/HinglishKosh">Contribute</a>
</div>
</div>
</div>
</footer>
</body>
</html>`;
}

function buildDefCard(label, content, borderColor, badgeBg, isDevanagari) {
    if (!content) return '';
    if (isDevanagari) {
        return `<div class="premium-card p-6 rounded-xl border-l-4 border-l-${borderColor}">
<div class="flex items-center gap-2 mb-3">
<span class="px-2 py-0.5 bg-${badgeBg} text-on-${badgeBg.replace('bg-', '')} rounded font-label-caps text-[10px] tracking-widest uppercase">${label}</span>
</div>
<div class="pl-4 border-l-2 border-primary">
<p class="font-hindi-entry text-2xl text-on-surface leading-normal">${content}</p>
</div>
</div>`;
    }
    return `<div class="premium-card p-6 rounded-xl border-l-4 border-l-${borderColor}">
<div class="flex items-center gap-2 mb-3">
<span class="px-2 py-0.5 bg-${badgeBg} text-on-${badgeBg.replace('bg-', '')} rounded font-label-caps text-[10px] tracking-widest uppercase">${label}</span>
</div>
<p class="font-body-lg text-body-lg text-on-surface leading-relaxed${label === 'Hinglish' ? ' italic' : ''}">${content}</p>
</div>`;
    // Note: badge text color classes like "text-on-primary-container" are simplified above;
    // in practice use class names that map correctly via the tailwind config.
    // For now the exact background classes are: bg-primary-container, bg-tertiary-container, bg-secondary-container.
}

function entryCard(entry, showFull) {
    const hindi = escapeHtml(entry.word_hindi || '');
    const roman = escapeHtml(entry.word_hinglish_roman || '');
    const def = entry.definition || '';
    const pos = entry.part_of_speech || '';
    const source = entry.source || '';
    const example = entry.example_sentence || '';
    const severity = entry.severity_score || 0;
    const isToxic = severity >= SAFE_THRESHOLD;

    // Search result — compact card
    if (!showFull) {
        let html = `<div class="premium-card p-5 rounded-xl ${isToxic ? 'border border-error-container' : ''}">`;
        html += `<a href="/word/${encodeURIComponent(entry.word_hinglish_roman || entry.word_hindi)}" class="block">`;
        html += `<div class="flex items-baseline gap-3 mb-1">`;
        html += `<span class="font-display-word text-2xl tracking-tight text-on-surface">${roman}</span>`;
        if (hindi) html += `<span class="font-hindi-entry text-lg text-on-surface-variant">${hindi}</span>`;
        html += `</div>`;
        if (pos || source) {
            html += `<div class="flex gap-2 mt-2">`;
            if (pos) html += `<span class="px-2 py-0.5 bg-secondary-container text-on-secondary-container rounded font-label-caps text-[10px] tracking-widest uppercase">${escapeHtml(pos)}</span>`;
            if (source) html += `<span class="px-2 py-0.5 bg-surface-container-high text-on-surface-variant rounded font-label-caps text-[10px] tracking-widest uppercase">${escapeHtml(source)}</span>`;
            html += `</div>`;
        }
        // Show first available definition as preview
        const defEn = entry.definition_en ? escapeHtml(entry.definition_en) : '';
        const defHi = entry.definition_hinglish ? escapeHtml(entry.definition_hinglish) : '';
        const defOrig = def ? escapeHtml(def) : '';
        const preview = defEn || defHi || defOrig;
        if (preview) {
            html += `<p class="mt-3 font-body-md text-body-md text-on-surface-variant line-clamp-2">${preview}</p>`;
        }
        html += `</a></div>`;
        return html;
    }

    // ─── Full word page ───
    const defEn = entry.definition_en ? escapeHtml(entry.definition_en) : '';
    const defHinglish = entry.definition_hinglish ? escapeHtml(entry.definition_hinglish) : '';
    const isWordNet = entry.source === 'WordNet';
    const defEscaped = def ? escapeHtml(def) : '';

    // Definition cards
    let defCards = '';
    defCards += buildDefCard('English', defEn, 'primary', 'primary-container', false);
    defCards += buildDefCard('Hinglish', defHinglish, 'tertiary', 'tertiary-container', false);
    if (def && isWordNet) {
        defCards += buildDefCard('Hindi', defEscaped, 'secondary', 'secondary-container', true);
    } else if (def && !isWordNet) {
        defCards += buildDefCard('Definition', defEscaped, 'secondary', 'secondary-container', false);
    }

    // Usage example
    let exHtml = '';
    if (example) {
        const escExample = escapeHtml(example);
        exHtml = `<section class="mb-16">
<h3 class="font-label-caps text-label-caps text-outline mb-4 uppercase tracking-widest">Usage Context</h3>
<blockquote class="relative p-10 bg-surface-container-low rounded-xl border-y border-outline-variant overflow-hidden">
<span class="material-symbols-outlined absolute -top-2 -left-2 text-surface-container-high text-8xl opacity-50 pointer-events-none select-none">format_quote</span>
<p class="relative z-10 font-body-lg text-body-lg md:text-2xl text-on-surface italic leading-relaxed text-center">${escExample}</p>
</blockquote>
</section>`;
    }

    // Badges
    let badges = '';
    if (pos) badges += `<span class="px-3 py-1 bg-secondary-container text-on-secondary-container rounded-full font-label-caps text-label-caps border border-outline-variant">${escapeHtml(pos)}</span>`;
    if (source) badges += `<span class="px-3 py-1 bg-surface-container-high text-on-surface-variant rounded-full font-label-caps text-label-caps border border-outline-variant">${escapeHtml(source)}</span>`;
    if (isToxic) badges += `<span class="px-3 py-1 bg-error-container text-on-error rounded-full font-label-caps text-label-caps border border-outline-variant">Flagged</span>`;

    // Related terms
    function chipRow(items, icon, label, colorClass, hoverBg) {
        if (!items || items.length === 0) return '';
        let chips = '';
        for (const r of items) {
            const roman = escapeHtml(r.word_hinglish_roman || '');
            const hindi = escapeHtml(r.word_hindi || '');
            const name = roman && hindi ? `${roman} (${hindi})` : roman || hindi;
            const uri = encodeURIComponent(r.word_hinglish_roman || r.word_hindi || '');
            chips += `<a class="px-3 py-1 bg-surface-container text-on-surface-variant hover:${hoverBg} transition-colors rounded-full text-sm font-medium border border-outline-variant" href="/word/${uri}">${name}</a>`;
        }
        return `<div class="premium-card p-6 rounded-xl flex flex-col gap-4">
<div class="flex items-center gap-2 ${colorClass}">
<span class="material-symbols-outlined">${icon}</span>
<h4 class="font-label-caps text-label-caps uppercase tracking-wider">${label}</h4>
</div>
<div class="flex flex-wrap gap-2">${chips}</div>
</div>`;
    }

    let relatedHtml = '';
    let sections = '';
    sections += chipRow(entry.same_synset, 'sync_alt', 'Synonyms', 'text-primary', 'bg-primary-fixed-dim');
    sections += chipRow(entry.broader_terms, 'expand_less', 'Broader Terms', 'text-secondary', 'bg-secondary-fixed-dim');
    sections += chipRow(entry.narrower_terms, 'expand_more', 'Narrower Terms', 'text-tertiary', 'bg-tertiary-fixed-dim');
    if (sections) {
        relatedHtml = `<section class="grid grid-cols-1 md:grid-cols-3 gap-gutter mb-16">${sections}</section>`;
    }

    return `<section class="mb-stack-lg border-b border-outline-variant pb-stack-lg">
<div class="flex flex-col md:flex-row md:items-baseline justify-between gap-4">
<div class="flex flex-col gap-2">
<h1 class="font-display-word text-display-word-mobile md:text-display-word text-on-surface">${roman}</h1>
<div class="font-hindi-entry text-hindi-entry text-on-surface-variant leading-none">${hindi}</div>
</div>
<div class="flex gap-2 flex-wrap">${badges}</div>
</div>
</section>
<!-- TODO: pronunciation/phonetic notation — use a Hindi LLM to generate later
<div class="mt-stack-md flex items-center gap-2 text-outline font-body-md">
  <span class="font-definition-num text-definition-num">PHONETIC</span>
  <span class="font-mono text-sm tracking-wide">/placeholder/</span>
  <button class="text-primary hover:scale-110 transition-transform" aria-label="Listen to pronunciation">
    <span class="material-symbols-outlined text-2xl">volume_up</span>
  </button>
</div>
-->
<section class="space-y-stack-lg mb-16">
<div class="flex items-center gap-4 mb-stack-md">
<h2 class="font-headline-md text-headline-md text-on-surface">Definitions</h2>
<div class="h-px flex-1 bg-outline-variant"></div>
</div>
${defCards}
</section>
${exHtml}
${relatedHtml}`;
}

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

function htmlResponse(html, status = 200) {
    return new Response(html, {
        status,
        headers: {
            'Content-Type': 'text/html; charset=utf-8',
            'Cache-Control': 'public, max-age=60, s-maxage=300',
        },
    });
}

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
