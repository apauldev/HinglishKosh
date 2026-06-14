import { error, redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { findBestMatch, getRelatedWords } from '$lib/server/db';

export const load: PageServerLoad = async ({ params, platform }) => {
  const db = platform?.env.DB;
  if (!db) {
    error(500, 'Database not available');
  }

  const slug = decodeURIComponent(params.slug || '');

  if (!slug.trim()) {
    error(404, 'Word not found');
  }

  const entry = await findBestMatch(db, slug);

  if (!entry) {
    error(404, `No entry found for "${slug}"`);
  }

  if (entry.word_hinglish_roman !== slug && entry.word_hindi !== slug) {
    const correctSlug = entry.word_hinglish_roman || encodeURIComponent(entry.word_hindi);
    redirect(301, `/word/${correctSlug}`);
  }

  const related = await getRelatedWords(db, entry.id);

  return {
    entry: {
      ...entry,
      ...related,
    },
  };
};
