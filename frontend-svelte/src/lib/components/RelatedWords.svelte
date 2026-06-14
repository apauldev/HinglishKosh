<script lang="ts">
  import type { RelatedWord } from '$lib/server/types';

  let {
    same_synset = [],
    broader = [],
    narrower = [],
  }: {
    same_synset?: RelatedWord[];
    broader?: RelatedWord[];
    narrower?: RelatedWord[];
  } = $props();
</script>

{#if same_synset.length > 0 || broader.length > 0 || narrower.length > 0}
  <div class="space-y-4">
    {#if same_synset.length > 0}
      <div>
        <h3 class="mb-2 text-sm font-semibold text-muted-foreground">Synonyms</h3>
        <div class="flex flex-wrap gap-2">
          {#each same_synset as word}
            <a
              href="/word/{word.word_hinglish_roman}"
              class="inline-flex items-center rounded-full border bg-muted px-3 py-1 text-sm transition-colors hover:bg-accent"
            >
              {word.word_hinglish_roman}
              <span class="ml-1 text-xs text-muted-foreground">{word.word_hindi}</span>
            </a>
          {/each}
        </div>
      </div>
    {/if}

    {#if broader.length > 0}
      <div>
        <h3 class="mb-2 text-sm font-semibold text-muted-foreground">Broader Terms</h3>
        <div class="flex flex-wrap gap-2">
          {#each broader as word}
            <a
              href="/word/{word.word_hinglish_roman}"
              class="inline-flex items-center rounded-full border bg-muted px-3 py-1 text-sm transition-colors hover:bg-accent"
            >
              {word.word_hinglish_roman}
              <span class="ml-1 text-xs text-muted-foreground">{word.word_hindi}</span>
            </a>
          {/each}
        </div>
      </div>
    {/if}

    {#if narrower.length > 0}
      <div>
        <h3 class="mb-2 text-sm font-semibold text-muted-foreground">Narrower Terms</h3>
        <div class="flex flex-wrap gap-2">
          {#each narrower as word}
            <a
              href="/word/{word.word_hinglish_roman}"
              class="inline-flex items-center rounded-full border bg-muted px-3 py-1 text-sm transition-colors hover:bg-accent"
            >
              {word.word_hinglish_roman}
              <span class="ml-1 text-xs text-muted-foreground">{word.word_hindi}</span>
            </a>
          {/each}
        </div>
      </div>
    {/if}
  </div>
{/if}
