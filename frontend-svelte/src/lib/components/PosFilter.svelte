<script lang="ts">
  import { page } from '$app/state';
  import type { PosCount } from '$lib/server/types';

  let { counts, activePos = '' }: { counts: PosCount[]; activePos?: string } = $props();

  const currentQuery = $derived(page.url.searchParams.get('q') || '');
</script>

<div class="space-y-6">
  <h3 class="text-[10px] font-bold tracking-[0.2em] text-muted-foreground uppercase flex items-center gap-2">
    <span class="w-1.5 h-1.5 bg-primary/40 rounded-full"></span>
    Grammar Filter
  </h3>
  <div class="space-y-1.5">
    {#each counts as { part_of_speech, count }}
      {@const isActive = activePos === part_of_speech}
      <a
        href="/search?q={encodeURIComponent(currentQuery)}&pos={part_of_speech}"
        class="flex items-center justify-between rounded-xl px-4 py-2.5 text-sm font-bold transition-all {isActive
          ? 'bg-primary text-white shadow-lg shadow-primary/20'
          : 'text-muted-foreground hover:bg-slate-100 dark:hover:bg-slate-900 hover:text-foreground'}"
      >
        <span class="capitalize">{part_of_speech}</span>
        <span class="inline-flex items-center justify-center rounded-lg px-2 py-0.5 text-[10px] font-extrabold {isActive ? 'bg-white/20 text-white' : 'bg-slate-100 dark:bg-slate-800 text-muted-foreground'}">{count}</span>
      </a>
    {/each}
    
    {#if activePos}
      <a
        href="/search?q={encodeURIComponent(currentQuery)}"
        class="flex items-center justify-center mt-6 py-2 px-4 rounded-xl border border-dashed border-border text-[10px] font-bold tracking-widest uppercase text-muted-foreground hover:border-primary hover:text-primary transition-all"
      >
        Clear Filter
      </a>
    {/if}
  </div>
</div>
