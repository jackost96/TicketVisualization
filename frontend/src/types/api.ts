export type StatusCategory = "todo" | "in_progress" | "done";

export interface User {
  id: number;
  email: string;
  display_name: string;
  is_active: boolean;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface Project {
  id: number;
  key: string;
  name: string;
  description: string | null;
  lead_user_id: number | null;
  is_archived: boolean;
}

export interface ProjectRole {
  id: number;
  name: string;
  description: string | null;
  is_system: boolean;
}

export interface ProjectRoleMember {
  project_id: number;
  role_id: number;
  user_id: number;
}

export interface IssueType {
  id: number;
  name: string;
  description: string | null;
  is_subtask: boolean;
  hierarchy_level: number;
}

export interface Status {
  id: number;
  name: string;
  category: StatusCategory;
  description: string | null;
}

export interface Priority {
  id: number;
  name: string;
  rank: number;
}

export interface Workflow {
  id: number;
  name: string;
  description: string | null;
  initial_status_id: number;
}

export interface WorkflowTransition {
  id: number;
  name: string;
  from_status_id: number | null;
  to_status_id: number;
}

export interface IssueLinkType {
  id: number;
  name: string;
  outward_name: string;
  inward_name: string;
  is_system: boolean;
}

export interface Issue {
  id: number;
  key: string;
  jira_key: string | null;
  project_id: number;
  issue_number: number;
  issue_type_id: number;
  status_id: number;
  workflow_id: number;
  summary: string;
  description: string | null;
  reporter_id: number | null;
  assignee_id: number | null;
  priority_id: number | null;
  parent_issue_id: number | null;
  resolution: string | null;
  resolved_at: string | null;
  due_date: string | null;
  story_points: number | null;
  labels: string[];
  created_at: string;
  updated_at: string;
}

export interface IssueHistoryEntry {
  id: number;
  issue_id: number;
  author_id: number | null;
  field_name: string;
  old_value: string | null;
  new_value: string | null;
  created_at: string;
}

export interface Comment {
  id: number;
  issue_id: number;
  author_id: number | null;
  body: string;
  created_at: string;
  updated_at: string;
}

export interface IssueLink {
  id: number;
  link_type_id: number;
  source_issue_id: number;
  target_issue_id: number;
  label: string;
}

export interface BoardSummary {
  id: number;
  project_id: number;
  name: string;
  swimlane_strategy: "none" | "assignee";
}

export interface BoardColumn {
  status_id: number;
  name: string;
  category: StatusCategory;
  position: number;
}

export interface Board extends BoardSummary {
  columns: BoardColumn[];
}

export interface Dashboard {
  id: number;
  owner_user_id: number;
  name: string;
  is_favorite: boolean;
}

export interface StatusCount {
  status_id: number;
  status_name: string;
  category: StatusCategory;
  count: number;
}

export interface FilterQuery {
  project?: string | null;
  status_id?: number | null;
  assignee_id?: number | null;
  reporter_id?: number | null;
  issue_type_id?: number | null;
  q?: string | null;
}

export interface SavedFilter {
  id: number;
  owner_user_id: number;
  name: string;
  query: FilterQuery;
}

export interface EffectivePermissions {
  project_id: number;
  permissions: string[];
}
