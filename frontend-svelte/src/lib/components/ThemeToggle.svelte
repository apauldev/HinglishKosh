<script lang="ts">
  const STORAGE_KEY = 'hinglishkosh-theme';

  let isDark = $state(false);

  function getPreferredTheme(): boolean {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'dark') return true;
    if (saved === 'light') return false;
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  function applyTheme(dark: boolean) {
    const root = document.documentElement;
    if (dark) {
      root.classList.add('dark');
      root.style.colorScheme = 'dark';
    } else {
      root.classList.remove('dark');
      root.style.colorScheme = 'light';
    }
    localStorage.setItem(STORAGE_KEY, dark ? 'dark' : 'light');
  }

  $effect(() => {
    isDark = getPreferredTheme();
    applyTheme(isDark);

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => {
      if (!localStorage.getItem(STORAGE_KEY)) {
        isDark = mediaQuery.matches;
        applyTheme(isDark);
      }
    };
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  });

  function handleToggle() {
    document.documentElement.classList.add('theme-transition');
    isDark = !isDark;
    applyTheme(isDark);
    setTimeout(() => {
      document.documentElement.classList.remove('theme-transition');
    }, 400);
  }

  let icon = $derived(isDark ? 'light_mode' : 'dark_mode');
  let label = $derived(isDark ? 'Switch to light mode' : 'Switch to dark mode');
</script>

<button
  onclick={handleToggle}
  class="material-symbols-outlined text-muted-foreground p-2 hover:bg-surface-container-high rounded-full transition-colors"
  aria-label={label}
>
  {icon}
</button>
