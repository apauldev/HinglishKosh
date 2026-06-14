import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { searchEntries } from '$lib/server/db';

export const GET: RequestHandler = async ({ url, platform }) => {
  const db = platform?.env.DB;
  if (!db) {
    return json({ error: 'Database not available' }, { status: 500 });
  }

  const q = url.searchParams.get('q') || '';
  const safe = url.searchParams.get('safe') === 'true';
  const limit = parseInt(url.searchParams.get('limit') || '20', 10);

  if (!q.trim()) {
    return json({ error: 'Missing search query' }, { status: 400 });
  }

  const result = await searchEntries(db, { q, safe, limit });

  return json(result, {
    headers: {
      'Cache-Control': 'public, max-age=60, s-maxage=300',
      'Access-Control-Allow-Origin': '*',
    },
  });
};
