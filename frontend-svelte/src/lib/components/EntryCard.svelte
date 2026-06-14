<script lang="ts">
  import type { Entry, EntryWithRelated } from '$lib/server/types';
  import { Badge } from '$lib/components/ui/badge';

  let { entry, full = false }: { entry: Entry | EntryWithRelated; full?: boolean } = $props();

  const SAFE_THRESHOLD = 0.5;
  const isToxic = $derived((entry.severity_score || 0) >= SAFE_THRESHOLD);

  function getDefinitionLabel(
    entry: Entry
  ): { label: string; content: string; isDevanagari: boolean; color: string }[] {
    const defs: { label: string; content: string; isDevanagari: boolean; color: string }[] = [];

    if (entry.definition_en) {
      defs.push({ label: 'English', content: entry.definition_en, isDevanagari: false, color: 'primary' });
    }
    if (entry.definition_hinglish) {
      defs.push({ label: 'Hinglish', content: entry.definition_hinglish, isDevanagari: false, color: 'tertiary' });
    }
    if (entry.definition) {
      defs.push({ label: 'Hindi', content: entry.definition, isDevanagari: true, color: 'secondary' });
    }

    return defs;
  }

  function getBadgeBg(color: string): string {
    const map: Record<string, string> = {
      primary: 'bg-primary-container',
      secondary: 'bg-secondary-container',
      tertiary: 'bg-surface-container-high',
    };
    return map[color] || 'bg-surface-container-high';
  }

  function getBadgeText(color: string): string {
    const map: Record<string, string> = {
      primary: 'text-on-secondary-container',
      secondary: 'text-on-secondary-container',
      tertiary: 'text-muted-foreground',
    };
    return map[color] || 'text-muted-foreground';
  }

  function getBorderColor(color: string): string {
    const map: Record<string, string> = {
      primary: 'border-l-primary',
      secondary: 'border-l-secondary',
      tertiary: 'border-l-accent',
    };
    return map[color] || 'border-l-primary';
  }
</script>

{#if full}
  {@const related = 'same_synset' in entry ? (entry as EntryWithRelated) : null}
  <article class="space-y-12 stagger-fade-in">
    <!-- Header -->
    <section class="border-b border-border pb-10">
      <div class="flex flex-col justify-between gap-6 md:flex-row md:items-end">
        <div class="space-y-2">
          <div class="flex items-center gap-3">
             <span class="text-[10px] font-bold tracking-[0.2em] text-primary uppercase bg-primary/5 px-2 py-0.5 rounded-md border border-primary/10">Lexicon Entry</span>
             {#if entry.part_of_speech}
               <span class="text-[10px] font-bold tracking-[0.2em] text-muted-foreground uppercase border border-border px-2 py-0.5 rounded-md">{entry.part_of_speech}</span>
             {/if}
          </div>
          <h1 class="font-display-word text-4xl md:text-7xl font-extrabold tracking-tight text-foreground leading-none">{entry.word_hinglish_roman}</h1>
          <div class="font-devanagari text-2xl md:text-5xl text-muted-foreground/60 leading-tight">{entry.word_hindi}</div>
        </div>
        
        <div class="flex flex-wrap gap-3">
          {#if entry.source}
            <div class="flex flex-col items-end">
              <span class="text-[10px] font-bold tracking-widest text-muted-foreground uppercase mb-1">Source</span>
              <span class="text-sm font-semibold px-4 py-1.5 bg-slate-100 dark:bg-slate-800 rounded-full border border-border">{entry.source}</span>
            </div>
          {/if}
          {#if isToxic}
            <div class="flex flex-col items-end">
              <span class="text-[10px] font-bold tracking-widest text-destructive uppercase mb-1">Status</span>
              <span class="text-sm font-semibold px-4 py-1.5 bg-destructive/10 text-destructive rounded-full border border-destructive/20">Flagged Content</span>
            </div>
          {/if}
        </div>
      </div>
    </section>

    <!-- Definitions -->
    <section class="max-w-4xl">
      <h2 class="text-[11px] font-bold tracking-[0.3em] uppercase text-muted-foreground mb-8 flex items-center gap-4">
        Definitions <div class="h-px flex-1 bg-border/50"></div>
      </h2>
      <div class="space-y-8">
        {#each getDefinitionLabel(entry) as def}
          <div class="relative pl-8 group">
            <div class="absolute left-0 top-0 bottom-0 w-1 bg-border group-hover:bg-primary transition-colors rounded-full"></div>
            <div class="flex flex-col gap-3">
              <div class="flex items-center gap-3">
                <span class="text-[10px] font-extrabold tracking-widest uppercase text-primary bg-primary/5 px-2 py-0.5 rounded border border-primary/10">{def.label}</span>
              </div>
              <p class="text-lg md:text-xl leading-relaxed text-foreground/90 {def.isDevanagari ? 'font-devanagari text-2xl md:text-3xl leading-snug text-foreground' : ''}">
                {def.content}
              </p>
            </div>
          </div>
        {/each}
      </div>
    </section>

    <!-- Example -->
    {#if entry.example_sentence}
      <section class="max-w-4xl">
        <h3 class="text-[11px] font-bold tracking-[0.3em] uppercase text-muted-foreground mb-8 flex items-center gap-4">
          Usage Context <div class="h-px flex-1 bg-border/50"></div>
        </h3>
        <div class="relative overflow-hidden rounded-3xl bg-slate-50 dark:bg-slate-900/40 p-10 md:p-14 border border-border shadow-inner">
          <span class="material-symbols-outlined absolute -top-4 -left-4 text-slate-200 dark:text-slate-800 text-[120px] opacity-50 select-none">format_quote</span>
          <p class="relative z-10 text-center font-medium text-xl md:text-3xl italic leading-relaxed text-foreground/80">
            "{entry.example_sentence}"
          </p>
        </div>
      </section>
    {/if}

    <!-- Related terms -->
    {#if related && (related.same_synset.length > 0 || related.broader.length > 0 || related.narrower.length > 0)}
      <section>
        <h4 class="text-[11px] font-bold tracking-[0.3em] uppercase text-muted-foreground mb-8 flex items-center gap-4">
          Lexical Relations <div class="h-px flex-1 bg-border/50"></div>
        </h4>
        <div class="grid grid-cols-1 gap-8 md:grid-cols-3">
          {#if related.same_synset.length > 0}
            <div class="space-y-4">
              <div class="flex items-center gap-2 text-primary">
                <span class="material-symbols-outlined text-xl">sync_alt</span>
                <span class="text-[11px] font-bold tracking-widest uppercase">Synonyms</span>
              </div>
              <div class="flex flex-wrap gap-2">
                {#each related.same_synset as word}
                  <a href="/word/{word.word_hinglish_roman}" class="px-3 py-1.5 text-sm font-semibold bg-card border border-border rounded-xl hover:border-primary hover:text-primary hover:shadow-md transition-all active:scale-95">
                    {word.word_hinglish_roman}
                  </a>
                {/each}
              </div>
            </div>
          {/if}

          {#if related.broader.length > 0}
            <div class="space-y-4">
              <div class="flex items-center gap-2 text-muted-foreground">
                <span class="material-symbols-outlined text-xl">expand_less</span>
                <span class="text-[11px] font-bold tracking-widest uppercase">Broader</span>
              </div>
              <div class="flex flex-wrap gap-2">
                {#each related.broader as word}
                  <a href="/word/{word.word_hinglish_roman}" class="px-3 py-1.5 text-sm font-semibold bg-card border border-border rounded-xl hover:border-primary hover:text-primary hover:shadow-md transition-all active:scale-95 text-muted-foreground hover:text-primary">
                    {word.word_hinglish_roman}
                  </a>
                {/each}
              </div>
            </div>
          {/if}

          {#if related.narrower.length > 0}
            <div class="space-y-4">
              <div class="flex items-center gap-2 text-muted-foreground">
                <span class="material-symbols-outlined text-xl">expand_more</span>
                <span class="text-[11px] font-bold tracking-widest uppercase">Narrower</span>
              </div>
              <div class="flex flex-wrap gap-2">
                {#each related.narrower as word}
                  <a href="/word/{word.word_hinglish_roman}" class="px-3 py-1.5 text-sm font-semibold bg-card border border-border rounded-xl hover:border-primary hover:text-primary hover:shadow-md transition-all active:scale-95 text-muted-foreground hover:text-primary">
                    {word.word_hinglish_roman}
                  </a>
                {/each}
              </div>
            </div>
          {/if}
        </div>
      </section>
    {/if}
  </article>
{:else}
  <a href="/word/{entry.word_hinglish_roman}" class="group block rounded-2xl border border-border bg-card p-6 shadow-sm transition-all duration-300 hover:shadow-premium hover:-translate-y-1 {isToxic ? 'border-l-4 border-l-destructive' : 'hover:border-primary/30'}">
    <div class="flex flex-col gap-1 mb-4">
      <div class="flex justify-between items-start">
        <span class="font-display-word text-2xl font-bold tracking-tight text-foreground group-hover:text-primary transition-colors">{entry.word_hinglish_roman}</span>
        {#if entry.part_of_speech}
          <span class="text-[9px] font-bold tracking-widest text-muted-foreground uppercase border border-border px-1.5 py-0.5 rounded-md">{entry.part_of_speech}</span>
        {/if}
      </div>
      {#if entry.word_hindi}
        <span class="font-devanagari text-lg text-muted-foreground/60">{entry.word_hindi}</span>
      {/if}
    </div>
    
    {#if entry.definition}
      <p class="font-medium text-sm text-muted-foreground line-clamp-2 leading-relaxed mb-4 group-hover:text-foreground/80 transition-colors">{entry.definition}</p>
    {/if}
    
    <div class="flex items-center justify-between pt-4 border-t border-border/50">
       <span class="text-[10px] font-bold tracking-widest text-muted-foreground uppercase group-hover:text-primary transition-colors">View Entry</span>
       <span class="material-symbols-outlined text-muted-foreground group-hover:text-primary transition-all group-hover:translate-x-1">arrow_forward</span>
    </div>
  </a>
{/if}
