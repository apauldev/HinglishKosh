<script lang="ts">
  import { page } from '$app/state';
  import ThemeToggle from './ThemeToggle.svelte';
  import SearchForm from './SearchForm.svelte';

  const navLinks = [
    { href: '/', label: 'Home' },
    { href: '/about', label: 'About' },
  ];

  let currentPage = $derived(
    page.url.pathname === '/' ? 'home' : page.url.pathname.split('/')[1] || 'home'
  );
</script>

<header class="sticky top-0 z-50 border-b border-border bg-surface transition-all duration-300">
  <div class="mx-auto flex h-14 md:h-20 max-w-7xl items-center justify-between px-4 md:px-12">
    <div class="flex items-center gap-4 md:gap-10">
      <a href="/" class="flex items-center gap-2 md:gap-3 group transition-transform active:scale-95" aria-label="HinglishKosh home">
        <div class="relative">
          <svg viewBox="0 0 36 36" class="h-8 w-8 md:h-10 md:w-10 shrink-0">
            <defs>
              <linearGradient id="logo-g" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
                <stop stop-color="#4648d4" />
                <stop offset="1" stop-color="#7c3aed" />
              </linearGradient>
            </defs>
            <rect width="36" height="36" rx="10" fill="url(#logo-g)" />
            <text x="18" y="25" text-anchor="middle" font-family="system-ui,-apple-system,sans-serif" font-weight="800" font-size="18" fill="white">हिं</text>
          </svg>
        </div>
        <div class="flex flex-col leading-tight">
          <span class="text-sm md:text-lg font-bold tracking-tight text-foreground">हिंग्लिशकोश</span>
          <span class="text-[8px] md:text-[10px] font-semibold tracking-[0.15em] md:tracking-[0.2em] text-muted-foreground uppercase">HinglishKosh</span>
        </div>
      </a>

      <nav class="hidden md:flex gap-6 lg:gap-8 items-center">
        {#each navLinks as link}
          <a
            href={link.href}
            class="relative text-xs lg:text-sm font-semibold tracking-wide transition-all hover:text-primary {currentPage === link.href.slice(1) || (link.href === '/' && currentPage === 'home')
              ? 'text-primary'
              : 'text-muted-foreground'}"
          >
            {link.label}
            {#if currentPage === link.href.slice(1) || (link.href === '/' && currentPage === 'home')}
              <span class="absolute -bottom-[18px] md:-bottom-[22px] left-0 right-0 h-0.5 md:h-1 bg-primary rounded-full"></span>
            {/if}
          </a>
        {/each}
      </nav>
    </div>

    <div class="flex items-center gap-2 md:gap-6">
      <div class="hidden sm:block w-44 md:w-72 lg:w-96">
        <SearchForm compact />
      </div>
      <a href="/search" class="sm:hidden flex items-center justify-center h-9 w-9 rounded-full hover:bg-surface-container-high transition-colors" aria-label="Search">
        <span class="material-symbols-outlined text-xl text-muted-foreground">search</span>
      </a>
      <ThemeToggle />
    </div>
  </div>
</header>
