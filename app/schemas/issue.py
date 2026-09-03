from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class IssueCreate(BaseModel):
    project_key: str
    issue_type_id: int
    summary: str
    description: str | None = None
    reporter_id: int | None = None
    assignee_id: int | None = None
    priority_id: int | None = None
    parent_issue_id: int | None = None
    due_date: date | None = None
    story_points: Decimal | None = None
    labels: list[str] = []


class IssueUpdate(BaseModel):
    summary: str | None = None
    description: str | None = None
    assignee_id: int | None = None
    priority_id: int | None = None
    parent_issue_id: int | None = None
    due_date: date | None = None
    story_points: Decimal | None = None
    labels: list[str] | None = None


class IssueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    jira_key: str | None = None
    project_id: int
    issue_number: int
    issue_type_id: int
    status_id: int
    workflow_id: int
    summary: str
    description: str | None = None
    reporter_id: int | None = None
    assignee_id: int | None = None
    priority_id: int | None = None
    parent_issue_id: int | None = None
    resolution: str | None = None
    resolved_at: datetime | None = None
    due_date: date | None = None
    story_points: Decimal | None = None
    labels: list[str]
    created_at: datetime
    updated_at: datetime


class IssueHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    issue_id: int
    author_id: int | None = None
    field_name: str
    old_value: str | None = None
    new_value: str | None = None
    created_at: datetime


class TransitionRequest(BaseModel):
    transition_id: int
