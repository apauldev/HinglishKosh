<script lang="ts">
  import { goto } from '$app/navigation';
  import type { Suggestion } from '$lib/server/types';

  let { compact = false, query = '' }: { compact?: boolean; query?: string } = $props();

  let searchQuery = $state('');
  let suggestions = $state<Suggestion[]>([]);
  let showSuggestions = $state(false);
  let selectedIndex = $state(-1);
  let debounceTimer: ReturnType<typeof setTimeout> | null = $state(null);

  $effect(() => {
    searchQuery = query || '';
  });

  async function fetchSuggestions(q: string) {
    if (q.length < 1) {
      suggestions = [];
      return;
    }

    try {
      const res = await fetch(`/api/suggest?q=${encodeURIComponent(q)}&limit=8`);
      const data = await res.json();
      suggestions = data.suggestions || [];
    } catch {
      suggestions = [];
    }
  }

  function handleInput(e: Event) {
    const target = e.target as HTMLInputElement;
    searchQuery = target.value;

    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      fetchSuggestions(searchQuery);
      showSuggestions = true;
      selectedIndex = -1;
    }, 120);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (!showSuggestions || suggestions.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedIndex = Math.min(selectedIndex + 1, suggestions.length - 1);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedIndex = Math.max(selectedIndex - 1, -1);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIndex >= 0) {
        const s = suggestions[selectedIndex];
        goto(`/word/${s.word_hinglish_roman}`);
        showSuggestions = false;
      } else if (searchQuery.trim()) {
        goto(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
        showSuggestions = false;
      }
    } else if (e.key === 'Escape') {
      showSuggestions = false;
    }
  }

  function handleSubmit(e: Event) {
    e.preventDefault();
    if (searchQuery.trim()) {
      goto(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
      showSuggestions = false;
    }
  }

  function handleFocus() {
    if (suggestions.length > 0) showSuggestions = true;
  }

  function handleBlur() {
    setTimeout(() => {
      showSuggestions = false;
    }, 200);
  }

  function highlightMatch(text: string, query: string): string {
    if (!query) return text;
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  }
</script>

<svelte:window
  onkeydown={(e) => {
    if (
      e.key === '/' &&
      !(e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement)
    ) {
      e.preventDefault();
      document.getElementById(compact ? 'search-input-compact' : 'search-input')?.focus();
    }
  }}
/>

<form onsubmit={handleSubmit} class="relative w-full" role="search" aria-label="Search the dictionary">
  <div class="relative flex items-center bg-card rounded-full shadow-sm transition-shadow duration-300 focus-within:shadow-lg focus-within:shadow-black/5 {compact ? 'h-10' : 'h-14'}">
    <span class="material-symbols-outlined {compact ? 'ml-4 text-lg' : 'ml-5 text-xl'} text-muted-foreground">search</span>
    <input
      id={compact ? 'search-input-compact' : 'search-input'}
      type="search"
      placeholder={compact ? 'Search...' : 'Search 209K+ words...'}
      value={searchQuery}
      oninput={handleInput}
      onkeydown={handleKeydown}
      onfocus={handleFocus}
      onblur={handleBlur}
      class="w-full bg-transparent border-none focus:ring-0 outline-none {compact ? 'px-3 text-sm' : 'px-4 text-base'} text-foreground placeholder:text-muted-foreground"
      autocomplete="off"
      aria-autocomplete="list"
      aria-controls="suggestions-list"
      aria-expanded={showSuggestions && suggestions.length > 0}
      aria-activedescendant={selectedIndex >= 0 ? `suggestion-${selectedIndex}` : undefined}
      role="combobox"
    />
    {#if !compact}
      <div class="pr-2 hidden md:flex items-center">
        <button
          type="submit"
          class="px-5 h-9 rounded-full bg-primary text-white text-sm font-semibold hover:bg-primary/90 transition-colors"
        >
          Search
        </button>
      </div>
    {/if}
  </div>

  {#if showSuggestions && suggestions.length > 0}
    <div
      id="suggestions-list"
      role="listbox"
      class="absolute top-full left-0 right-0 z-[100] mt-2 overflow-hidden rounded-xl border border-border bg-white dark:bg-[#1d1b20] shadow-xl"
    >
      <div class="max-h-[360px] overflow-y-auto">
        {#each suggestions as suggestion, i}
          <a
            href="/word/{suggestion.word_hinglish_roman}"
            role="option"
            id="suggestion-{i}"
            aria-selected={i === selectedIndex}
            class="flex items-center justify-between px-5 py-3 transition-colors {i === selectedIndex ? 'bg-primary text-white font-bold' : 'text-foreground hover:bg-slate-100 dark:hover:bg-slate-800'}"
            onclick={() => {
              showSuggestions = false;
            }}
          >
            <span class="text-sm font-semibold">{@html highlightMatch(suggestion.word_hinglish_roman, searchQuery)}</span>
            <span class="font-devanagari text-base text-muted-foreground">{@html highlightMatch(suggestion.word_hindi, searchQuery)}</span>
          </a>
          {#if i < suggestions.length - 1}
            <div class="mx-4 h-px bg-border/50"></div>
          {/if}
        {/each}
      </div>
    </div>
  {/if}
</form>
