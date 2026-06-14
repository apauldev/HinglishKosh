<script lang="ts">
  import EntryCard from '$lib/components/EntryCard.svelte';

  let { data } = $props();
</script>

<svelte:head>
  <title>{data.entry.word_hindi} ({data.entry.word_hinglish_roman}) — HinglishKosh</title>
  <meta
    name="description"
    content="{data.entry.word_hindi} ({data.entry
      .word_hinglish_roman}) — {data.entry.definition?.substring(0, 150)}"
  />
</svelte:head>

<div class="mx-auto max-w-4xl px-4 py-12 md:px-12">
  <EntryCard entry={data.entry} full />
</div>
