from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.issue import Issue, IssueHistory
from app.models.project import Project
from app.models.status import Status, StatusCategory
from app.models.user import User
from app.schemas.issue import IssueCreate, IssueRead, IssueUpdate
from app.services import issue_key_service, workflow_service


class IssueNotFoundError(Exception):
    pass


def serialize_issue(issue: Issue) -> IssueRead:
    return IssueRead(
        id=issue.id,
        key=issue_key_service.format_key(issue.project.key, issue.issue_number),
        jira_key=issue.jira_key,
        project_id=issue.project_id,
        issue_number=issue.issue_number,
        issue_type_id=issue.issue_type_id,
        status_id=issue.status_id,
        workflow_id=issue.workflow_id,
        summary=issue.summary,
        description=issue.description,
        reporter_id=issue.reporter_id,
        assignee_id=issue.assignee_id,
        priority_id=issue.priority_id,
        parent_issue_id=issue.parent_issue_id,
        resolution=issue.resolution,
        resolved_at=issue.resolved_at,
        due_date=issue.due_date,
        story_points=issue.story_points,
        labels=issue.labels,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
    )


def get_issue_by_key(db: Session, key: str) -> Issue:
    project_key, issue_number = issue_key_service.parse_key(key)
    issue = (
        db.query(Issue)
        .options(joinedload(Issue.project))
        .join(Project, Issue.project_id == Project.id)
        .filter(Project.key == project_key, Issue.issue_number == issue_number)
        .one_or_none()
    )
    if issue is None:
        raise IssueNotFoundError(f"Issue '{key}' not found")
    return issue


def create_issue(db: Session, payload: IssueCreate, actor: User) -> Issue:
    project = db.query(Project).filter(Project.key == payload.project_key).one_or_none()
    if project is None:
        raise IssueNotFoundError(f"Project '{payload.project_key}' not found")

    workflow = workflow_service.resolve_workflow_for_issue_type(db, project, payload.issue_type_id)
    issue_number = issue_key_service.allocate_issue_number(db, project)

    issue = Issue(
        project_id=project.id,
        issue_number=issue_number,
        issue_type_id=payload.issue_type_id,
        status_id=workflow.initial_status_id,
        workflow_id=workflow.id,
        summary=payload.summary,
        description=payload.description,
        reporter_id=payload.reporter_id if payload.reporter_id is not None else actor.id,
        assignee_id=payload.assignee_id,
        priority_id=payload.priority_id,
        parent_issue_id=payload.parent_issue_id,
        due_date=payload.due_date,
        story_points=payload.story_points,
        labels=payload.labels,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue


_TRACKED_FIELDS = [
    "summary",
    "description",
    "assignee_id",
    "priority_id",
    "parent_issue_id",
    "due_date",
    "story_points",
    "labels",
]


def update_issue(db: Session, issue: Issue, payload: IssueUpdate, actor: User) -> Issue:
    changes = payload.model_dump(exclude_unset=True)
    now = datetime.now(timezone.utc)
    for field in _TRACKED_FIELDS:
        if field not in changes:
            continue
        old_value = getattr(issue, field)
        new_value = changes[field]
        if old_value == new_value:
            continue
        setattr(issue, field, new_value)
        db.add(
            IssueHistory(
                issue_id=issue.id,
                author_id=actor.id,
                field_name=field,
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(new_value) if new_value is not None else None,
                created_at=now,
            )
        )
    db.commit()
    db.refresh(issue)
    return issue


def delete_issue(db: Session, issue: Issue) -> None:
    db.delete(issue)
    db.commit()


def list_issues(
    db: Session,
    project_key: str | None = None,
    status_id: int | None = None,
    assignee_id: int | None = None,
    reporter_id: int | None = None,
    issue_type_id: int | None = None,
    q: str | None = None,
    open_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[Issue]:
    query = db.query(Issue).options(joinedload(Issue.project))
    if project_key is not None:
        query = query.join(Project, Issue.project_id == Project.id).filter(
            Project.key == project_key
        )
    if status_id is not None:
        query = query.filter(Issue.status_id == status_id)
    if assignee_id is not None:
        query = query.filter(Issue.assignee_id == assignee_id)
    if reporter_id is not None:
        query = query.filter(Issue.reporter_id == reporter_id)
    if issue_type_id is not None:
        query = query.filter(Issue.issue_type_id == issue_type_id)
    if q:
        query = query.filter(Issue.search_vector.op("@@")(func.plainto_tsquery("english", q)))
    if open_only:
        query = query.join(Status, Issue.status_id == Status.id).filter(
            Status.category != StatusCategory.done
        )
    return query.order_by(Issue.id).offset(offset).limit(limit).all()


def list_issues_assigned_to(
    db: Session, user_id: int, open_only: bool = False, limit: int = 50, offset: int = 0
) -> list[Issue]:
    return list_issues(db, assignee_id=user_id, open_only=open_only, limit=limit, offset=offset)
