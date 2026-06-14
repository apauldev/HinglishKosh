import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getSuggestions } from '$lib/server/db';

export const GET: RequestHandler = async ({ url, platform }) => {
  const db = platform?.env.DB;
  if (!db) {
    return json({ error: 'Database not available' }, { status: 500 });
  }

  const q = url.searchParams.get('q') || '';
  const limit = parseInt(url.searchParams.get('limit') || '8', 10);

  if (!q.trim() || q.trim().length < 1) {
    return json({ suggestions: [] });
  }

  const result = await getSuggestions(db, { q, limit });

  return json(result, {
    headers: {
      'Cache-Control': 'public, max-age=60, s-maxage=300',
      'Access-Control-Allow-Origin': '*',
    },
  });
};
