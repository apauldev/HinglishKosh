export interface Entry {
  id: string;
  word_hindi: string;
  word_hinglish_roman: string;
  definition: string;
  part_of_speech: string | null;
  example_sentence: string | null;
  source: string | null;
  confidence_score: number | null;
  severity_score: number | null;
  toxicity_flags: string | null;
  synonyms: string | null;
  antonyms: string | null;
  tags: string | null;
  head_word: string | null;
  definition_en: string | null;
  definition_hinglish: string | null;
}

export interface Suggestion {
  word_hindi: string;
  word_hinglish_roman: string;
}

export interface RelatedWord {
  word_hindi: string;
  word_hinglish_roman: string;
  id: string;
}

export interface EntryWithRelated extends Entry {
  same_synset: RelatedWord[];
  broader: RelatedWord[];
  narrower: RelatedWord[];
}

export interface Stats {
  total_entries: number;
  safe_entries: number;
  toxic_entries: number;
  total_relation_links: number;
  sources: SourceCount[];
  pos_distribution: PosCount[];
}

export interface SourceCount {
  source: string;
  count: number;
}

export interface PosCount {
  part_of_speech: string;
  count: number;
}

export interface SearchResult {
  query: string;
  count: number;
  results: Entry[];
  fallback?: boolean;
}

export interface SuggestResult {
  query: string;
  suggestions: Suggestion[];
}

export interface LookupResult {
  query: string;
  count: number;
  results: Entry[];
}

export interface SearchParams {
  q: string;
  safe?: boolean;
  limit?: number;
}

export interface SuggestParams {
  q: string;
  limit?: number;
}

export interface LookupParams {
  word: string;
  safe?: boolean;
  limit?: number;
}
