import { apiFetch } from "./client";
import type { Dashboard, StatusCount } from "@/types/api";

export function getHomeDashboard(): Promise<Dashboard> {
  return apiFetch<Dashboard>("/dashboards/home");
}

export function getStatusCounts(): Promise<StatusCount[]> {
  return apiFetch<StatusCount[]>("/dashboards/panels/status-counts");
}

export function listDashboards(): Promise<Dashboard[]> {
  return apiFetch<Dashboard[]>("/dashboards");
}

export function getDashboard(id: number): Promise<Dashboard> {
  return apiFetch<Dashboard>(`/dashboards/${id}`);
}

export function createDashboard(name: string): Promise<Dashboard> {
  return apiFetch<Dashboard>("/dashboards", { method: "POST", body: { name } });
}

export function renameDashboard(id: number, name: string): Promise<Dashboard> {
  return apiFetch<Dashboard>(`/dashboards/${id}`, { method: "PATCH", body: { name } });
}

export function deleteDashboard(id: number): Promise<void> {
  return apiFetch<void>(`/dashboards/${id}`, { method: "DELETE" });
}

export function favoriteDashboard(id: number): Promise<Dashboard> {
  return apiFetch<Dashboard>(`/dashboards/${id}/favorite`, { method: "POST" });
}
