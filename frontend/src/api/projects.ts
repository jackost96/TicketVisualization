import { apiFetch } from "./client";
import type { EffectivePermissions, Project, ProjectRoleMember } from "@/types/api";

export function listProjects(): Promise<Project[]> {
  return apiFetch<Project[]>("/projects");
}

export function getProject(key: string): Promise<Project> {
  return apiFetch<Project>(`/projects/${key}`);
}

export function createProject(payload: { key: string; name: string; description?: string }): Promise<Project> {
  return apiFetch<Project>("/projects", { method: "POST", body: payload });
}

export function getMyPermissions(key: string): Promise<EffectivePermissions> {
  return apiFetch<EffectivePermissions>(`/projects/${key}/permissions/me`);
}

export function listRoleMembers(projectKey: string, roleId: number): Promise<ProjectRoleMember[]> {
  return apiFetch<ProjectRoleMember[]>(`/projects/${projectKey}/roles/${roleId}/members`);
}

export function addRoleMember(
  projectKey: string,
  roleId: number,
  userId: number,
): Promise<ProjectRoleMember> {
  return apiFetch<ProjectRoleMember>(`/projects/${projectKey}/roles/${roleId}/members`, {
    method: "POST",
    body: { user_id: userId },
  });
}

export function removeRoleMember(projectKey: string, roleId: number, userId: number): Promise<void> {
  return apiFetch<void>(`/projects/${projectKey}/roles/${roleId}/members/${userId}`, {
    method: "DELETE",
  });
}
