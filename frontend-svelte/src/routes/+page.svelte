<script lang="ts">
  import SearchForm from '$lib/components/SearchForm.svelte';

  const quickLinks = [
    { word: 'namaste', label: 'namaste' },
    { word: 'paani', label: 'paani' },
    { word: 'chai', label: 'chai' },
    { word: 'pyaar', label: 'pyaar' },
    { word: 'dhanyavaad', label: 'dhanyavaad' },
  ];

  const features = [
    {
      title: 'English',
      description:
        'Every entry has an English translation — simple, clear, and ready for non-Hindi speakers who want to understand what a word means.',
      color: 'bg-primary',
    },
    {
      title: 'Hindi (Devanagari)',
      description:
        'The original Devanagari definition sourced from Hindi WordNet (IIT Bombay) — authoritative and academically verified.',
      color: 'bg-secondary',
    },
    {
      title: 'Hinglish (Roman)',
      description:
        "Hindi meanings written in Roman script — for the diaspora and learners who speak Hindi but can't read Devanagari.",
      color: 'bg-muted',
    },
  ];

  const stats = [
    { value: '209k', label: 'ENTRIES' },
    { value: '153k', label: 'WORDNET (HINDI)' },
    { value: '56k', label: 'WIKTIONARY' },
    { value: '40k+', label: 'SYNSET RELATIONS' },
  ];
</script>

<svelte:head>
  <title>HinglishKosh — The Open Hinglish Dictionary</title>
  <meta
    name="description"
    content="A comprehensive open-source Hinglish-English dictionary with 209,462 entries. Search Hindi words, English definitions, and Hinglish romanizations."
  />
</svelte:head>

<div class="mx-auto overflow-hidden">
  <!-- Hero & Search Section -->
  <section class="relative bg-slate-50/50 dark:bg-slate-950/20 border-b border-border">
    <div class="hero-pattern"></div>
    <div class="relative z-10 mx-auto max-w-7xl px-6 md:px-12">
      <div class="flex flex-col items-center py-12 text-center md:py-36">
        <div class="mb-10 inline-flex items-center gap-2 rounded-full bg-primary/5 px-4 py-1.5 border border-primary/10 stagger-fade-in">
          <span class="material-symbols-outlined text-[18px] text-primary">analytics</span>
          <span class="text-[11px] font-bold tracking-widest text-primary uppercase">
            209K+ ENTRIES · OPEN SOURCE · FREE
          </span>
        </div>
        
        <h1 class="font-display-word text-display-word-mobile md:text-display-word mb-12 max-w-4xl tracking-tight leading-[1.1] stagger-fade-in">
          Decode Hindi like a <span class="text-primary relative inline-block">
            native speaker.
            <svg class="absolute -bottom-2 left-0 w-full h-2 text-primary/20" viewBox="0 0 100 10" preserveAspectRatio="none">
              <path d="M0 5 Q 25 0 50 5 T 100 5" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>
            </svg>
          </span>
        </h1>

        <div class="relative w-full max-w-3xl stagger-fade-in" style="animation-delay: 0.2s">
          <div class="mb-10">
            <SearchForm />
          </div>

          <div class="flex flex-wrap justify-center gap-3 items-center">
            <span class="text-[10px] font-bold tracking-[0.2em] text-muted-foreground uppercase mr-2">
              QUICK SEARCH:
            </span>
            {#each quickLinks as link (link.word)}
              <a
                href="/word/{link.word}"
                class="rounded-full border border-border bg-card px-5 py-2 text-sm font-semibold text-foreground transition-all hover:border-primary hover:text-primary hover:shadow-md active:scale-95"
              >
                {link.label}
              </a>
            {/each}
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Feature Grid -->
  <section class="mx-auto max-w-7xl px-6 py-16 md:py-24 md:px-12">
    <div class="mb-10 md:mb-16 max-w-2xl">
      <h2 class="font-headline-md text-2xl md:text-4xl font-bold mb-3 md:mb-4 tracking-tight">Designed for your linguistic journey</h2>
      <p class="text-lg text-muted-foreground leading-relaxed">
        Three definitions for every word — tailored for every type of learner and background.
      </p>
    </div>
    <div class="grid gap-8 md:grid-cols-3">
      {#each features as feature (feature.title)}
        <div
          class="flex flex-col rounded-2xl border border-border bg-card p-10 hover-lift shadow-sm group"
        >
          <div
            class="mb-8 flex h-14 w-14 items-center justify-center rounded-2xl {feature.color} text-white shadow-lg transition-transform group-hover:scale-110 group-hover:rotate-3"
          >
            {#if feature.title === 'English'}
              <span class="material-symbols-outlined text-3xl">translate</span>
            {:else if feature.title === 'Hindi (Devanagari)'}
              <span class="material-symbols-outlined text-3xl">menu_book</span>
            {:else}
              <span class="material-symbols-outlined text-3xl">public</span>
            {/if}
          </div>
          <h3 class="font-headline-md text-2xl font-bold mb-4 tracking-tight">{feature.title}</h3>
          <p class="flex-grow text-muted-foreground leading-relaxed">{feature.description}</p>
        </div>
      {/each}
    </div>
  </section>

  <!-- Stats Counter Section -->
  <section class="mx-auto max-w-7xl px-6 md:px-12">
    <div class="my-20 rounded-3xl bg-slate-900 dark:bg-slate-900/50 p-12 md:p-16 relative overflow-hidden">
      <div class="absolute inset-0 opacity-10 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:20px_20px]"></div>
      <div class="relative z-10 grid grid-cols-2 gap-8 md:gap-12 md:grid-cols-4 stagger-fade-in">
        {#each stats as stat (stat.label)}
          <div class="text-center">
            <div class="font-display-word text-4xl md:text-5xl font-bold text-primary mb-2 tracking-tighter">{stat.value}</div>
            <div class="text-[10px] font-bold tracking-[0.2em] text-slate-400 uppercase">
              {stat.label}
            </div>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- Why HinglishKosh Section -->
  <section class="mx-auto max-w-7xl px-6 py-24 md:px-12">
    <div class="mx-auto max-w-4xl bg-card border border-border rounded-3xl p-10 md:p-20 shadow-premium relative">
      <div class="absolute top-0 right-0 p-8 opacity-5">
        <span class="material-symbols-outlined text-9xl">auto_stories</span>
      </div>
      <h2 class="font-headline-md text-3xl md:text-4xl font-extrabold mb-8 tracking-tight">Why HinglishKosh?</h2>
      <div class="space-y-6 text-lg leading-relaxed text-muted-foreground">
        <p>
          Over <strong class="text-foreground font-bold underline decoration-primary/30 decoration-4 underline-offset-4">600 million people</strong> in India communicate daily in
          Hinglish — a natural blend of Hindi and English written in the Roman script. It's how you text
          your friends, type on WhatsApp, and scroll through social media.
        </p>
        <p>
          Yet before this, there was <strong class="text-foreground font-bold">no open dictionary</strong> for
          it. Academic resources use ISO 15919 transliteration (<em class="italic">cāy</em>,
          <em class="italic">pānī</em>) — accurate but nobody types that way. Commercial keyboards
          keep their dictionaries closed.
        </p>
        <div class="pt-4">
          <p class="font-headline-md text-3xl font-bold text-primary tracking-tight">HinglishKosh fixes that.</p>
        </div>
      </div>
    </div>
  </section>
</div>
