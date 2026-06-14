import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { searchEntries } from '$lib/server/db';
import type { PosCount } from '$lib/server/types';

export const load: PageServerLoad = async ({ url, platform }) => {
  const db = platform?.env.DB;
  if (!db) {
    error(500, 'Database not available');
  }

  const q = url.searchParams.get('q') || '';
  const safe = url.searchParams.get('safe') === 'true';
  const limit = parseInt(url.searchParams.get('limit') || '20', 10);
  const pos = url.searchParams.get('pos') || '';

  if (!q.trim()) {
    return {
      query: '',
      results: [],
      count: 0,
      fallback: false,
      posCounts: [],
      activePos: '',
    };
  }

  const result = await searchEntries(db, { q, safe, limit });

  let filteredResults = result.results;
  let posCounts: PosCount[] = [];

  if (pos) {
    const posMap = new Map<string, number>();
    for (const entry of result.results) {
      if (entry.part_of_speech) {
        posMap.set(entry.part_of_speech, (posMap.get(entry.part_of_speech) || 0) + 1);
      }
    }
    posCounts = Array.from(posMap.entries())
      .map(([part_of_speech, count]) => ({ part_of_speech, count }))
      .sort((a, b) => b.count - a.count);

    filteredResults = result.results.filter((e) => e.part_of_speech === pos);
  } else {
    const posMap = new Map<string, number>();
    for (const entry of result.results) {
      if (entry.part_of_speech) {
        posMap.set(entry.part_of_speech, (posMap.get(entry.part_of_speech) || 0) + 1);
      }
    }
    posCounts = Array.from(posMap.entries())
      .map(([part_of_speech, count]) => ({ part_of_speech, count }))
      .sort((a, b) => b.count - a.count);
  }

  return {
    query: result.query,
    results: filteredResults,
    count: filteredResults.length,
    fallback: result.fallback || false,
    posCounts,
    activePos: pos,
  };
};
