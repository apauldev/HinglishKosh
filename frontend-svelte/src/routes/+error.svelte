<script lang="ts">
  import { page } from '$app/state';
  import { Button } from '$lib/components/ui/button';
</script>

<div class="flex min-h-[70vh] flex-col items-center justify-center px-6 text-center">
  <div class="relative mb-8">
     <div class="font-display-word text-[120px] md:text-[180px] font-extrabold text-primary/10 leading-none select-none">404</div>
     <div class="absolute inset-0 flex items-center justify-center">
        <span class="material-symbols-outlined text-primary text-6xl">search_off</span>
     </div>
  </div>
  <h1 class="text-3xl md:text-4xl font-extrabold tracking-tight text-foreground">Lost in translation?</h1>
  <p class="mt-4 text-lg text-muted-foreground max-w-md leading-relaxed font-medium">
    {#if page.error?.message}
      {page.error.message}
    {:else}
      We couldn't find the page or word you're looking for. It might have been moved or never existed.
    {/if}
  </p>
  <div class="mt-12 flex flex-col md:flex-row gap-4 w-full max-w-sm">
    <a href="/" class="flex-1">
      <Button class="w-full h-12 rounded-xl font-bold shadow-lg shadow-primary/20">Return Home</Button>
    </a>
    <a href="/search" class="flex-1">
      <Button variant="outline" class="w-full h-12 rounded-xl font-bold">Try Search</Button>
    </a>
  </div>
</div>
