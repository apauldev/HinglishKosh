import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export const SAFE_THRESHOLD = 0.5;

export function sanitizeQuery(query: string): string {
  return query
    .replace(/[^\w\s]/g, '')
    .trim()
    .split(/\s+/)
    .map((token) => `${token}*`)
    .join(' ');
}
