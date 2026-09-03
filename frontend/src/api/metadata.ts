import { apiFetch } from "./client";
import type { IssueLinkType, IssueType, Priority, ProjectRole, Status, Workflow } from "@/types/api";

export function listIssueTypes(): Promise<IssueType[]> {
  return apiFetch<IssueType[]>("/issue-types");
}

export function listStatuses(): Promise<Status[]> {
  return apiFetch<Status[]>("/statuses");
}

export function listPriorities(): Promise<Priority[]> {
  return apiFetch<Priority[]>("/priorities");
}

export function listWorkflows(): Promise<Workflow[]> {
  return apiFetch<Workflow[]>("/workflows");
}

export function listIssueLinkTypes(): Promise<IssueLinkType[]> {
  return apiFetch<IssueLinkType[]>("/issue-link-types");
}

export function listProjectRoles(): Promise<ProjectRole[]> {
  return apiFetch<ProjectRole[]>("/project-roles");
}
