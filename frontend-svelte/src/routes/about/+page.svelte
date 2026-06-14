<script lang="ts">
  const stats = [
    { value: '209,462', label: 'Dictionary Entries' },
    { value: '40,000+', label: 'Synset Relations' },
    { value: '2', label: 'Data Sources' },
  ];

  const sources = [
    {
      name: 'Hindi WordNet',
      description: 'IIT Bombay',
    },
    {
      name: 'Wiktionary',
      description: 'Open-source dictionary',
    },
  ];

  const techStack = [
    { name: 'Cloudflare Pages', description: 'Hosting & CDN' },
    { name: 'D1', description: 'Serverless SQLite' },
    { name: 'FTS5', description: 'Full-text search' },
    { name: 'Tailwind CSS', description: 'Styling' },
    { name: 'Python', description: 'Data processing' },
    { name: 'SQLite', description: 'Local development' },
  ];

  const credits = [
    {
      title: 'Data Sources',
      items: [
        { name: 'Hindi WordNet (IIT Bombay)', url: '#' },
        { name: 'Wiktionary', url: 'https://wiktionary.org' },
      ],
    },
    {
      title: 'License',
      items: [{ name: 'GPL v3.0', url: '#' }],
    },
    {
      title: 'Stack',
      items: [
        { name: 'SvelteKit', url: 'https://kit.svelte.dev' },
        { name: 'Cloudflare', url: 'https://cloudflare.com' },
      ],
    },
    {
      title: 'Contribute',
      items: [
        { name: 'GitHub', url: 'https://github.com' },
        { name: 'Report Issues', url: 'https://github.com' },
      ],
    },
  ];
</script>

<svelte:head>
  <title>About — HinglishKosh</title>
  <meta
    name="description"
    content="Learn about HinglishKosh, the open-source Hinglish-English dictionary."
  />
</svelte:head>

<div class="mx-auto overflow-hidden">
  <!-- Hero Section -->
  <section class="relative bg-slate-50/50 dark:bg-slate-950/20 border-b border-border">
    <div class="hero-pattern"></div>
    <div class="relative z-10 mx-auto max-w-7xl px-6 py-20 text-center md:px-12 md:py-32">
      <h1 class="font-display-word text-display-word-mobile md:text-display-word mb-6 tracking-tight leading-tight stagger-fade-in">
        Democratizing the <span class="text-primary underline decoration-primary/20 decoration-8 underline-offset-8">Hinglish Lexicon.</span>
      </h1>
      <p class="mx-auto max-w-3xl text-lg md:text-xl text-muted-foreground leading-relaxed stagger-fade-in" style="animation-delay: 0.1s">
        HinglishKosh is an open-source dictionary built for the 600M+ people who speak Hinglish every day — providing clarity in the way India actually communicates.
      </p>
    </div>
  </section>

  <div class="mx-auto max-w-7xl px-6 md:px-12">
    <!-- Stats Grid -->
    <section class="py-16">
      <div class="grid grid-cols-1 gap-8 md:grid-cols-3 stagger-fade-in" style="animation-delay: 0.2s">
        {#each stats as stat (stat.label)}
          <div class="rounded-2xl border border-border bg-card p-10 text-center shadow-sm hover-lift group">
            <div class="font-display-word text-4xl font-bold text-primary group-hover:scale-110 transition-transform">{stat.value}</div>
            <div class="text-[10px] font-bold tracking-[0.2em] text-muted-foreground uppercase mt-3">
              {stat.label}
            </div>
          </div>
        {/each}
      </div>
    </section>

    <!-- Methodology -->
    <section class="py-24 border-t border-border/50">
      <div class="grid gap-20 md:grid-cols-2">
        <div>
          <h2 class="font-headline-md text-3xl font-extrabold mb-8 tracking-tight flex items-center gap-3">
             <span class="p-2 bg-primary/10 text-primary rounded-xl"><span class="material-symbols-outlined">experiment</span></span>
             Methodology
          </h2>
          <div class="space-y-6 text-lg text-muted-foreground leading-relaxed">
            <p>
              HinglishKosh combines data from two authoritative sources to create a comprehensive
              Hinglish-English dictionary.
            </p>
            <div class="space-y-4">
              {#each sources as source (source.name)}
                <div class="flex items-start gap-4 p-5 bg-card border border-border rounded-2xl shadow-sm hover:border-primary/30 transition-colors">
                  <div class="mt-1.5 h-3 w-3 rounded-full bg-primary/40"></div>
                  <div>
                    <div class="font-bold text-foreground text-base tracking-tight">{source.name}</div>
                    <div class="text-sm font-medium mt-1">{source.description}</div>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        </div>

        <div>
          <h2 class="font-headline-md text-3xl font-extrabold mb-8 tracking-tight flex items-center gap-3">
             <span class="p-2 bg-accent/10 text-accent rounded-xl"><span class="material-symbols-outlined">architecture</span></span>
             Approach
          </h2>
          <div class="space-y-6 text-lg text-muted-foreground leading-relaxed">
            <p>Every entry in HinglishKosh includes definitions in three formats to ensure accessibility for all:</p>
            <div class="space-y-4">
               <div class="flex items-center gap-4 p-5 bg-card border border-border rounded-2xl">
                  <span class="material-symbols-outlined text-primary">translate</span>
                  <span class="font-bold text-foreground text-base">English — <span class="text-muted-foreground font-medium">For non-Hindi speakers</span></span>
               </div>
               <div class="flex items-center gap-4 p-5 bg-card border border-border rounded-2xl">
                  <span class="material-symbols-outlined text-secondary">menu_book</span>
                  <span class="font-bold text-foreground text-base font-devanagari">Hindi (Devanagari) — <span class="text-muted-foreground font-medium font-sans">The original script</span></span>
               </div>
               <div class="flex items-center gap-4 p-5 bg-card border border-border rounded-2xl">
                  <span class="material-symbols-outlined text-accent">public</span>
                  <span class="font-bold text-foreground text-base">Hinglish (Roman) — <span class="text-muted-foreground font-medium">How India actually types</span></span>
               </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Tech Stack -->
    <section class="py-24 border-t border-border/50">
      <div class="mb-12">
        <h2 class="font-headline-md text-3xl font-extrabold tracking-tight">Tech Stack</h2>
        <p class="text-muted-foreground mt-2 font-medium">Built with modern, serverless infrastructure for performance and scale.</p>
      </div>
      <div class="grid grid-cols-2 gap-6 md:grid-cols-3">
        {#each techStack as tech (tech.name)}
          <div class="rounded-2xl border border-border bg-card p-6 shadow-sm hover:shadow-premium transition-all group">
            <div class="font-bold text-foreground text-base group-hover:text-primary transition-colors">{tech.name}</div>
            <div class="text-sm font-medium text-muted-foreground mt-1">{tech.description}</div>
          </div>
        {/each}
      </div>
    </section>

    <!-- Credits -->
    <section class="py-24 border-t border-border/50">
      <h2 class="font-headline-md text-3xl font-extrabold mb-12 tracking-tight">Credits & Community</h2>
      <div class="grid grid-cols-2 gap-12 md:grid-cols-4">
        {#each credits as section (section.title)}
          <div class="space-y-6">
            <h3 class="text-[10px] font-bold tracking-[0.2em] text-muted-foreground uppercase flex items-center gap-2">
              <span class="w-1.5 h-1.5 bg-primary/40 rounded-full"></span>
              {section.title}
            </h3>
            <ul class="space-y-4">
              {#each section.items as item (item.name)}
                <li>
                  <a
                    href={item.url}
                    class="text-sm font-bold text-foreground/70 hover:text-primary transition-all flex items-center gap-2"
                    target="_blank"
                    rel="noopener"
                  >
                    {item.name}
                    <span class="material-symbols-outlined text-[14px] opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all">north_east</span>
                  </a>
                </li>
              {/each}
            </ul>
          </div>
        {/each}
      </div>
    </section>
  </div>
</div>
