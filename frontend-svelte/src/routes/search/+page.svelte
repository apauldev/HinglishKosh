<script lang="ts">
  import SearchForm from '$lib/components/SearchForm.svelte';
  import EntryCard from '$lib/components/EntryCard.svelte';
  import PosFilter from '$lib/components/PosFilter.svelte';
  import { Badge } from '$lib/components/ui/badge';

  let { data } = $props();
</script>

<svelte:head>
  <title>Search: {data.query} — HinglishKosh</title>
  <meta
    name="description"
    content="Search results for '{data.query}' in HinglishKosh dictionary."
  />
</svelte:head>

<div class="mx-auto max-w-7xl px-6 py-12 md:px-12">
  <div class="mb-12 max-w-3xl relative z-30">
    <SearchForm query={data.query} />
  </div>

  {#if data.query}
    <div class="mb-10 flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-border pb-8">
      <div class="flex items-center gap-3">
        <h1 class="text-2xl md:text-3xl font-extrabold tracking-tight">Results for <span class="text-primary">"{data.query}"</span></h1>
        {#if data.fallback}
          <span class="text-[10px] font-bold tracking-widest uppercase bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-md border border-border">Fuzzy match</span>
        {/if}
      </div>
      <div class="text-[11px] font-bold tracking-[0.2em] text-muted-foreground uppercase">
        Found {data.count} lexicon entries
      </div>
    </div>
  {/if}

  {#if data.results.length > 0}
    <div class="grid gap-12 lg:grid-cols-12 stagger-fade-in">
      {#if data.posCounts.length > 0}
        <aside class="lg:col-span-3">
          <div class="sticky top-32">
            <PosFilter counts={data.posCounts} activePos={data.activePos} />
          </div>
        </aside>
      {/if}

      <div class="space-y-6 {data.posCounts.length > 0 ? 'lg:col-span-9' : 'lg:col-span-12'}">
        {#each data.results as entry (entry.id)}
          <EntryCard {entry} />
        {/each}
      </div>
    </div>
  {:else if data.query}
    <div class="py-24 text-center">
      <div class="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-slate-50 dark:bg-slate-900 border border-border mb-6">
         <span class="material-symbols-outlined text-muted-foreground text-4xl">search_off</span>
      </div>
      <h2 class="text-3xl font-extrabold tracking-tight mb-2">No results found</h2>
      <p class="text-lg text-muted-foreground max-w-md mx-auto">We couldn't find anything matching your search. Try checking your spelling or use a more common term.</p>
      <div class="mt-10">
         <a href="/" class="text-sm font-bold text-primary hover:underline underline-offset-4 flex items-center justify-center gap-2">
           <span class="material-symbols-outlined text-sm">arrow_back</span>
           Back to Home
         </a>
      </div>
    </div>
  {/if}
</div>
