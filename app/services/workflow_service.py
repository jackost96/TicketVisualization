"""Workflow state machine: resolves which workflow governs a new issue, and validates/applies
status transitions. Pure functions operating on a Session — no HTTP/FastAPI concerns, so they're
unit-testable without spinning up the API layer."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.issue import Issue, IssueHistory
from app.models.project import Project
from app.models.status import StatusCategory
from app.models.user import User
from app.models.workflow import Workflow, WorkflowSchemeEntry, WorkflowTransition


class WorkflowError(Exception):
    pass


class NoWorkflowSchemeError(WorkflowError):
    pass


class InvalidTransitionError(WorkflowError):
    def __init__(self, message: str, valid_transitions: list[WorkflowTransition]):
        super().__init__(message)
        self.valid_transitions = valid_transitions


def resolve_workflow_for_issue_type(db: Session, project: Project, issue_type_id: int) -> Workflow:
    """(project, issue_type) -> workflow, via the project's workflow scheme. Falls back to the
    scheme's default entry (issue_type_id IS NULL) if no type-specific entry exists."""
    if project.default_workflow_scheme_id is None:
        raise NoWorkflowSchemeError(f"Project '{project.key}' has no workflow scheme configured")

    entry = (
        db.query(WorkflowSchemeEntry)
        .filter(
            WorkflowSchemeEntry.workflow_scheme_id == project.default_workflow_scheme_id,
            WorkflowSchemeEntry.issue_type_id == issue_type_id,
        )
        .one_or_none()
    )
    if entry is None:
        entry = (
            db.query(WorkflowSchemeEntry)
            .filter(
                WorkflowSchemeEntry.workflow_scheme_id == project.default_workflow_scheme_id,
                WorkflowSchemeEntry.issue_type_id.is_(None),
            )
            .one_or_none()
        )
    if entry is None:
        raise NoWorkflowSchemeError(
            f"No workflow scheme entry (specific or default) for issue type {issue_type_id} "
            f"in project '{project.key}'"
        )
    return db.get(Workflow, entry.workflow_id)


def get_available_transitions(db: Session, issue: Issue) -> list[WorkflowTransition]:
    return (
        db.query(WorkflowTransition)
        .filter(
            WorkflowTransition.workflow_id == issue.workflow_id,
            (WorkflowTransition.from_status_id == issue.status_id)
            | (WorkflowTransition.from_status_id.is_(None)),
        )
        .all()
    )


def apply_transition(db: Session, issue: Issue, transition_id: int, actor: User) -> Issue:
    valid = get_available_transitions(db, issue)
    transition = next((t for t in valid if t.id == transition_id), None)
    if transition is None:
        raise InvalidTransitionError(
            f"Transition {transition_id} is not valid from issue {issue.id}'s current status",
            valid_transitions=valid,
        )

    old_status_id = issue.status_id
    new_status = transition.to_status
    now = datetime.now(timezone.utc)

    issue.status_id = transition.to_status_id
    if new_status.category == StatusCategory.done:
        if issue.resolved_at is None:
            issue.resolved_at = now
    else:
        issue.resolved_at = None

    db.add(
        IssueHistory(
            issue_id=issue.id,
            author_id=actor.id,
            field_name="status",
            old_value=str(old_status_id),
            new_value=str(issue.status_id),
        )
    )
    db.flush()
    return issue
