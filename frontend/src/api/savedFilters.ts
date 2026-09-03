import { apiFetch } from "./client";
import type { FilterQuery, SavedFilter } from "@/types/api";

export function listSavedFilters(): Promise<SavedFilter[]> {
  return apiFetch<SavedFilter[]>("/saved-filters");
}

export function createSavedFilter(name: string, query: FilterQuery): Promise<SavedFilter> {
  return apiFetch<SavedFilter>("/saved-filters", { method: "POST", body: { name, query } });
}

export function deleteSavedFilter(id: number): Promise<void> {
  return apiFetch<void>(`/saved-filters/${id}`, { method: "DELETE" });
}
