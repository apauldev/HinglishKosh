import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { lookupWord } from '$lib/server/db';

export const GET: RequestHandler = async ({ url, platform }) => {
  const db = platform?.env.DB;
  if (!db) {
    return json({ error: 'Database not available' }, { status: 500 });
  }

  const word = url.searchParams.get('word') || '';
  const safe = url.searchParams.get('safe') === 'true';
  const limit = parseInt(url.searchParams.get('limit') || '10', 10);

  if (!word.trim()) {
    return json({ error: 'Missing word parameter' }, { status: 400 });
  }

  const result = await lookupWord(db, { word, safe, limit });

  return json(result, {
    headers: {
      'Cache-Control': 'public, max-age=60, s-maxage=300',
      'Access-Control-Allow-Origin': '*',
    },
  });
};
