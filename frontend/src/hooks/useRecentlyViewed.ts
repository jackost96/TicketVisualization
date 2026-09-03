import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "recently_viewed_issues";
const MAX_ENTRIES = 20;

function readStoredKeys(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

/** Tracks the last-viewed issue keys in localStorage -- client-side only, doesn't sync across
 * devices/browsers. See the implementation plan for why this is scoped as a prototype
 * simplification rather than a backend table. */
export function useRecentlyViewed() {
  const [keys, setKeys] = useState<string[]>(() => readStoredKeys());

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(keys));
  }, [keys]);

  const markViewed = useCallback((issueKey: string) => {
    setKeys((prev) => [issueKey, ...prev.filter((k) => k !== issueKey)].slice(0, MAX_ENTRIES));
  }, []);

  return { recentKeys: keys, markViewed };
}
