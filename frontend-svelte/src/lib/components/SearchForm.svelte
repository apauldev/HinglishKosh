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

<form onsubmit={handleSubmit} class="relative w-full group" role="search">
  <div class="relative flex items-center bg-card border border-border rounded-full transition-all duration-300 shadow-sm focus-within:shadow-premium focus-within:border-primary/30 {compact ? 'h-11' : 'h-14 md:h-16'}">
    <span class="material-symbols-outlined {compact ? 'ml-4 text-lg' : 'ml-5 text-2xl'} text-muted-foreground transition-colors group-focus-within:text-primary">search</span>
    <input
      id={compact ? 'search-input-compact' : 'search-input'}
      type="search"
      placeholder={compact ? 'Search dictionary...' : 'Search for words in English, Hindi, or Hinglish...'}
      value={searchQuery}
      oninput={handleInput}
      onkeydown={handleKeydown}
      onfocus={handleFocus}
      onblur={handleBlur}
      class="w-full bg-transparent border-none focus:ring-0 outline-none {compact ? 'px-3 text-sm' : 'px-5 text-lg'} text-foreground placeholder:text-muted-foreground/50 font-medium"
      autocomplete="off"
    />
    {#if !compact}
      <div class="pr-3 hidden md:flex items-center gap-2">
        <button
          type="submit"
          class="px-8 h-10 md:h-11 rounded-full bg-primary text-white text-sm font-bold hover:bg-primary/90 transition-all active:scale-95 shadow-md shadow-primary/10"
        >
          Search
        </button>
      </div>
    {/if}
  </div>

  {#if showSuggestions && suggestions.length > 0}
    <div
      class="absolute top-full left-0 right-0 z-[9999] mt-3 overflow-hidden rounded-2xl border border-border bg-card shadow-2xl animate-in fade-in slide-in-from-top-2 duration-200"
    >
      <div class="max-h-[380px] overflow-y-auto py-2">
        {#each suggestions as suggestion, i}
          <a
            href="/word/{suggestion.word_hinglish_roman}"
            class="flex items-center justify-between px-5 py-3.5 transition-all {i === selectedIndex ? 'bg-primary/5' : 'hover:bg-slate-50 dark:hover:bg-slate-900/50'}"
            onclick={() => {
              showSuggestions = false;
            }}
          >
            <div class="flex flex-col">
              <span class="text-base font-bold text-foreground group-hover:text-primary transition-colors"
                >{@html highlightMatch(suggestion.word_hinglish_roman, searchQuery)}</span
              >
              <span class="text-[10px] font-bold tracking-widest text-muted-foreground/60 uppercase mt-0.5">ROMAN</span>
            </div>
            <div class="flex flex-col items-end">
              <span class="font-devanagari text-lg text-primary/80"
                >{@html highlightMatch(suggestion.word_hindi, searchQuery)}</span
              >
              <span class="text-[10px] font-bold tracking-widest text-muted-foreground/60 uppercase mt-0.5">HINDI</span>
            </div>
          </a>
          {#if i < suggestions.length - 1}
            <div class="mx-5 h-px bg-border/50"></div>
          {/if}
        {/each}
      </div>
      <div class="bg-slate-50 dark:bg-slate-900/50 px-5 py-2.5 border-t border-border flex justify-between items-center">
        <span class="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Results for "{searchQuery}"</span>
        <div class="flex gap-3">
           <span class="flex items-center gap-1 text-[10px] font-bold text-muted-foreground uppercase"><kbd class="px-1 bg-card border border-border rounded">↓</kbd> Navigate</span>
           <span class="flex items-center gap-1 text-[10px] font-bold text-muted-foreground uppercase"><kbd class="px-1 bg-card border border-border rounded">↵</kbd> Select</span>
        </div>
      </div>
    </div>
  {/if}
</form>
