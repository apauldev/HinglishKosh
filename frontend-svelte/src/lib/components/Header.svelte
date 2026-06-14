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

<header class="sticky top-0 z-50 border-b border-border glass transition-all duration-300">
  <div class="mx-auto flex h-20 max-w-7xl items-center justify-between px-6 md:px-12">
    <div class="flex items-center gap-10">
      <a href="/" class="flex items-center gap-3 group transition-transform hover:scale-[1.02]" aria-label="HinglishKosh home">
        <div class="relative">
          <svg viewBox="0 0 36 36" class="h-10 w-10 shrink-0 drop-shadow-sm">
            <defs>
              <linearGradient id="logo-g" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
                <stop stop-color="#4f46e5" />
                <stop offset="1" stop-color="#8b5cf6" />
              </linearGradient>
            </defs>
            <rect width="36" height="36" rx="10" fill="url(#logo-g)" />
            <text x="18" y="25" text-anchor="middle" font-family="system-ui,-apple-system,sans-serif" font-weight="800" font-size="18" fill="white">हिं</text>
          </svg>
          <div class="absolute -inset-1 bg-primary/20 blur-lg rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
        </div>
        <div class="flex flex-col leading-tight">
          <span class="text-lg font-extrabold tracking-tight text-foreground">हिंग्लिशकोश</span>
          <span class="text-[10px] font-bold tracking-[0.2em] text-muted-foreground uppercase opacity-80">HinglishKosh</span>
        </div>
      </a>

      <nav class="hidden lg:flex gap-8 items-center">
        {#each navLinks as link}
          <a
            href={link.href}
            class="relative text-sm font-semibold tracking-wide transition-all hover:text-primary {currentPage === link.href.slice(1) || (link.href === '/' && currentPage === 'home')
              ? 'text-primary'
              : 'text-muted-foreground'}"
          >
            {link.label}
            {#if currentPage === link.href.slice(1) || (link.href === '/' && currentPage === 'home')}
              <span class="absolute -bottom-[29px] left-0 right-0 h-1 bg-primary rounded-full"></span>
            {/if}
          </a>
        {/each}
      </nav>
    </div>

    <div class="flex items-center gap-6">
      <div class="hidden md:block w-72 lg:w-96">
        <SearchForm compact />
      </div>
      <div class="h-6 w-px bg-border hidden md:block"></div>
      <ThemeToggle />
    </div>
  </div>
</header>
