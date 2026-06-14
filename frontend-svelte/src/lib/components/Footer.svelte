<script lang="ts">
  const currentYear = new Date().getFullYear();
</script>

<footer class="border-t border-border bg-slate-50/50 dark:bg-slate-950/20 glass mt-20">
  <div class="mx-auto max-w-7xl px-8 py-16">
    <div class="flex flex-col md:flex-row justify-between items-start gap-12">
      <div class="flex flex-col gap-6">
        <a href="/" class="flex items-center gap-3 group">
          <svg viewBox="0 0 36 36" class="h-9 w-9 shrink-0 drop-shadow-sm">
            <rect width="36" height="36" rx="10" fill="url(#logo-g)" />
            <text x="18" y="25" text-anchor="middle" font-family="system-ui,-apple-system,sans-serif" font-weight="800" font-size="18" fill="white">हिं</text>
          </svg>
          <span class="text-xl font-extrabold tracking-tight text-foreground">हिंग्लिशकोश</span>
        </a>
        <p class="max-w-xs text-sm font-medium text-muted-foreground leading-relaxed">
          The open-source Hinglish-English dictionary. Built with passion for how India actually types.
        </p>
        <div class="text-[10px] font-bold tracking-[0.2em] text-muted-foreground uppercase flex items-center gap-2">
          &copy; {currentYear} HinglishKosh <span class="w-1 h-1 bg-muted-foreground/30 rounded-full"></span> GPL v3
        </div>
      </div>

      <div class="grid grid-cols-2 gap-16 md:gap-24">
        <div class="flex flex-col gap-4">
          <h3 class="text-[10px] font-bold tracking-[0.3em] text-foreground uppercase mb-2">PROJECT</h3>
          <a href="/about" class="text-sm font-bold text-muted-foreground hover:text-primary transition-colors">About</a>
          <a href="https://github.com/apauldev/HinglishKosh" class="text-sm font-bold text-muted-foreground hover:text-primary transition-colors" target="_blank" rel="noopener">GitHub</a>
          <a href="https://github.com/apauldev/HinglishKosh/blob/main/LICENSE" class="text-sm font-bold text-muted-foreground hover:text-primary transition-colors" target="_blank" rel="noopener">License</a>
        </div>
        <div class="flex flex-col gap-4">
          <h3 class="text-[10px] font-bold tracking-[0.3em] text-foreground uppercase mb-2">COMMUNITY</h3>
          <a href="https://github.com/apauldev/HinglishKosh/issues" class="text-sm font-bold text-muted-foreground hover:text-primary transition-colors" target="_blank" rel="noopener">Feedback</a>
          <a href="https://github.com/apauldev/HinglishKosh" class="text-sm font-bold text-muted-foreground hover:text-primary transition-colors" target="_blank" rel="noopener">Contribute</a>
        </div>
      </div>
    </div>
  </div>
</footer>
