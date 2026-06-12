// HinglishKosh — Theme toggle + autocomplete
(function () {
  'use strict';

  // ─── Theme ───

  const htmlEl = document.documentElement;
  const toggleBtn = document.getElementById('theme-toggle');
  const STORAGE_KEY = 'hinglishkosh-theme';

  function getPreferredTheme() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function getSavedTheme() {
    return localStorage.getItem(STORAGE_KEY);
  }

  function applyTheme(theme) {
    const isDark = theme === 'dark';
    htmlEl.classList.toggle('dark', isDark);
    localStorage.setItem(STORAGE_KEY, theme);
  }

  function initTheme() {
    const saved = getSavedTheme();
    const theme = saved || getPreferredTheme();
    applyTheme(theme);
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const isDark = htmlEl.classList.contains('dark');
      // Add transition class temporarily
      document.body.classList.add('theme-transition');
      applyTheme(isDark ? 'light' : 'dark');
      setTimeout(() => document.body.classList.remove('theme-transition'), 400);
    });
  }

  initTheme();

  // Listen for system preference changes (only if user hasn't saved a preference)
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!getSavedTheme()) {
      applyTheme(e.matches ? 'dark' : 'light');
    }
  });

  // ─── Copyright year ───
  const yearEl = document.getElementById('cYear');
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

  // ─── Autocomplete ───

  const searchInput = document.getElementById('search-input');
  const suggestionsEl = document.getElementById('suggestions');
  let suggestionIndex = -1;
  let suggestionData = [];
  let debounceTimer = null;

  // ─── Keyboard shortcut: / to focus search ───
  document.addEventListener('keydown', function (e) {
    const input = document.getElementById('search-input');
    if (e.key === '/' && !e.ctrlKey && !e.metaKey && document.activeElement !== input) {
      e.preventDefault();
      input?.focus();
    }
  });

  if (!searchInput || !suggestionsEl) return;

  searchInput.addEventListener('input', function () {
    const q = this.value.trim();
    clearTimeout(debounceTimer);
    if (q.length < 1) {
      hideSuggestions();
      return;
    }
    debounceTimer = setTimeout(() => fetchSuggestions(q), 120);
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

  document.addEventListener('click', function (e) {
    if (!searchInput.contains(e.target) && !suggestionsEl.contains(e.target)) {
      hideSuggestions();
    }
  });

  function fetchSuggestions(q) {
    fetch('/api/suggest?q=' + encodeURIComponent(q) + '&limit=8')
      .then(r => r.json())
      .then(data => {
        suggestionData = data.suggestions || [];
        renderSuggestions(q);
      })
      .catch(() => {});
  }

  function renderSuggestions(query) {
    suggestionIndex = -1;
    if (suggestionData.length === 0) {
      hideSuggestions();
      return;
    }
    let html = '';
    const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const re = new RegExp('(' + escapedQuery + ')', 'gi');

    for (let i = 0; i < suggestionData.length; i++) {
      const s = suggestionData[i];
      const roman = s.word_hinglish_roman || '';
      const hindi = s.word_hindi || '';
      const href = '/word/' + encodeURIComponent(roman || hindi);

      const highlightedHindi = hindi.replace(re, '<mark class="bg-primary-fixed text-primary rounded-sm px-0.5">$1</mark>');
      const highlightedRoman = roman.replace(re, '<mark class="bg-primary-fixed text-primary rounded-sm px-0.5">$1</mark>');

      html += '<a href="' + href + '" class="suggestion-item" data-index="' + i + '">' +
        '<span class="suggestion-hindi">' + highlightedHindi + '</span>' +
        '<span class="suggestion-roman">' + highlightedRoman + '</span>' +
        '</a>';
    }

    suggestionsEl.innerHTML = html;
    suggestionsEl.hidden = false;
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

})();
