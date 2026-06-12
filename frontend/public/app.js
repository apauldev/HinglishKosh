// HinglishKosh frontend JS — autocomplete + search enhancements

(function () {
    'use strict';

    const searchInput = document.getElementById('search-input');
    const suggestionsEl = document.getElementById('suggestions');
    let suggestionIndex = -1;
    let suggestionData = [];
    let debounceTimer = null;

    if (!searchInput || !suggestionsEl) return;

    // ─── Autocomplete ───

    searchInput.addEventListener('input', function () {
        const q = this.value.trim();
        clearTimeout(debounceTimer);

        if (q.length < 1) {
            hideSuggestions();
            return;
        }

        debounceTimer = setTimeout(() => fetchSuggestions(q), 150);
    });

    searchInput.addEventListener('keydown', function (e) {
        const items = suggestionsEl.querySelectorAll('.suggestion-item');

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            suggestionIndex = Math.min(suggestionIndex + 1, items.length - 1);
            updateActiveItem(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            suggestionIndex = Math.max(suggestionIndex - 1, -1);
            updateActiveItem(items);
        } else if (e.key === 'Enter') {
            if (suggestionIndex >= 0 && suggestionData[suggestionIndex]) {
                e.preventDefault();
                const s = suggestionData[suggestionIndex];
                window.location.href = '/word/' + encodeURIComponent(s.word_hinglish_roman || s.word_hindi);
            }
        } else if (e.key === 'Escape') {
            hideSuggestions();
        }
    });

    // Close suggestions on click outside
    document.addEventListener('click', function (e) {
        if (!searchInput.contains(e.target) && !suggestionsEl.contains(e.target)) {
            hideSuggestions();
        }
    });

    function fetchSuggestions(q) {
        const url = '/api/suggest?q=' + encodeURIComponent(q) + '&limit=8';

        fetch(url)
            .then(r => r.json())
            .then(data => {
                suggestionData = data.suggestions || [];
                renderSuggestions(q);
            })
            .catch(() => { /* silently fail — search still works */ });
    }

    function renderSuggestions(query) {
        suggestionIndex = -1;

        if (suggestionData.length === 0) {
            hideSuggestions();
            return;
        }

        let html = '';
        for (const s of suggestionData) {
            const roman = s.word_hinglish_roman || '';
            const hindi = s.word_hindi || '';
            const href = '/word/' + encodeURIComponent(roman || hindi);

            // Highlight matching portion
            const re = new RegExp('(' + query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
            const highlightedRoman = roman.replace(re, '<strong>$1</strong>');
            const highlightedHindi = hindi.replace(re, '<strong>$1</strong>');

            html += '<a href="' + href + '" class="suggestion-item" data-index="' + (suggestionData.indexOf(s)) + '">' +
                '<span class="suggestion-hindi">' + highlightedHindi + '</span>' +
                '<span class="suggestion-roman">' + highlightedRoman + '</span>' +
                '</a>';
        }

        suggestionsEl.innerHTML = html;
        suggestionsEl.hidden = false;

        // Click handler for suggestion items (prevents navigation, uses direct link)
        suggestionsEl.querySelectorAll('.suggestion-item').forEach(el => {
            el.addEventListener('mousedown', function (e) {
                // Use mousedown instead of click to fire before blur
                // The href already handles navigation
            });
        });
    }

    function updateActiveItem(items) {
        items.forEach((el, i) => {
            el.classList.toggle('active', i === suggestionIndex);
            if (i === suggestionIndex) {
                el.scrollIntoView({ block: 'nearest' });
            }
        });
    }

    function hideSuggestions() {
        suggestionsEl.hidden = true;
        suggestionData = [];
        suggestionIndex = -1;
    }

    // ─── Keyboard shortcut: focus search ───
    document.addEventListener('keydown', function (e) {
        if (e.key === '/' && !e.ctrlKey && !e.metaKey && document.activeElement !== searchInput) {
            e.preventDefault();
            searchInput.focus();
        }
    });

})();
