import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getStats } from '$lib/server/db';

export const GET: RequestHandler = async ({ platform }) => {
  const db = platform?.env.DB;
  if (!db) {
    return json({ error: 'Database not available' }, { status: 500 });
  }

  const result = await getStats(db);

  return json(result, {
    headers: {
      'Cache-Control': 'public, max-age=60, s-maxage=300',
      'Access-Control-Allow-Origin': '*',
    },
  });
};
