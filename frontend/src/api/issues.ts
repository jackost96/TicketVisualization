import { apiFetch } from "./client";
import type { Comment, Issue, IssueHistoryEntry, IssueLink, WorkflowTransition } from "@/types/api";

export type ListIssuesParams = {
  project?: string;
  status_id?: number;
  assignee_id?: number;
  reporter_id?: number;
  issue_type_id?: number;
  q?: string;
  open_only?: boolean;
  limit?: number;
  offset?: number;
};

export function listIssues(params: ListIssuesParams = {}): Promise<Issue[]> {
  return apiFetch<Issue[]>("/issues", { query: params });
}

export function getMyIssues(params: { open_only?: boolean; limit?: number; offset?: number } = {}): Promise<Issue[]> {
  return apiFetch<Issue[]>("/issues/me", { query: params });
}

export function getIssue(key: string): Promise<Issue> {
  return apiFetch<Issue>(`/issues/${key}`);
}

export interface CreateIssuePayload {
  project_key: string;
  issue_type_id: number;
  summary: string;
  description?: string;
  reporter_id?: number;
  assignee_id?: number;
  priority_id?: number;
  parent_issue_id?: number;
  due_date?: string;
  story_points?: number;
  labels?: string[];
}

export function createIssue(payload: CreateIssuePayload): Promise<Issue> {
  return apiFetch<Issue>("/issues", { method: "POST", body: payload });
}

export function updateIssue(key: string, payload: Partial<CreateIssuePayload>): Promise<Issue> {
  return apiFetch<Issue>(`/issues/${key}`, { method: "PATCH", body: payload });
}

export function deleteIssue(key: string): Promise<void> {
  return apiFetch<void>(`/issues/${key}`, { method: "DELETE" });
}

export function getTransitions(key: string): Promise<WorkflowTransition[]> {
  return apiFetch<WorkflowTransition[]>(`/issues/${key}/transitions`);
}

export function doTransition(key: string, transitionId: number): Promise<Issue> {
  return apiFetch<Issue>(`/issues/${key}/transitions`, {
    method: "POST",
    body: { transition_id: transitionId },
  });
}

export function getHistory(key: string): Promise<IssueHistoryEntry[]> {
  return apiFetch<IssueHistoryEntry[]>(`/issues/${key}/history`);
}

export function listComments(key: string): Promise<Comment[]> {
  return apiFetch<Comment[]>(`/issues/${key}/comments`);
}

export function createComment(key: string, body: string): Promise<Comment> {
  return apiFetch<Comment>(`/issues/${key}/comments`, { method: "POST", body: { body } });
}

export function listLinks(key: string): Promise<IssueLink[]> {
  return apiFetch<IssueLink[]>(`/issues/${key}/links`);
}

export function createLink(
  key: string,
  payload: { link_type_id: number; target_key: string; direction: "outward" | "inward" },
): Promise<IssueLink> {
  return apiFetch<IssueLink>(`/issues/${key}/links`, { method: "POST", body: payload });
}
