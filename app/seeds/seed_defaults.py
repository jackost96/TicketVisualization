"""Seeds the reference/config data that both Phase 1 CRUD and the Jira migration
depend on already existing: statuses, a default workflow + scheme, system issue-link
types, issue types, priorities, project roles, and the permission catalog/scheme.

Run with: python -m app.seeds.seed_defaults
Safe to re-run: every insert is a get-or-create keyed on the natural unique column.
"""
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import (
    IssueLinkType,
    IssueType,
    Permission,
    PermissionScheme,
    PermissionSchemeGrant,
    Priority,
    ProjectRole,
    Status,
    Workflow,
    WorkflowScheme,
    WorkflowSchemeEntry,
    WorkflowTransition,
)
from app.models.status import StatusCategory


def _get_or_create(session: Session, model, defaults: dict | None = None, **lookup):
    instance = session.query(model).filter_by(**lookup).one_or_none()
    if instance is not None:
        return instance, False
    instance = model(**{**lookup, **(defaults or {})})
    session.add(instance)
    session.flush()
    return instance, True


def seed_statuses(session: Session) -> dict[str, Status]:
    rows = [
        ("Open", StatusCategory.todo),
        ("In Progress", StatusCategory.in_progress),
        ("Under Investigation", StatusCategory.in_progress),
        ("QA", StatusCategory.in_progress),
        ("Closed", StatusCategory.done),
    ]
    statuses = {}
    for name, category in rows:
        status, _ = _get_or_create(session, Status, name=name, defaults={"category": category})
        statuses[name] = status
    return statuses


def seed_priorities(session: Session) -> None:
    for rank, name in enumerate(["Minor", "Major", "Critical", "Blocker"]):
        _get_or_create(session, Priority, name=name, defaults={"rank": rank})


def seed_issue_types(session: Session) -> None:
    rows = [
        ("Epic", False, 1),
        ("Story", False, 0),
        ("Bug", False, 0),
        ("Task", False, 0),
        ("Sub-task", True, -1),
    ]
    for name, is_subtask, hierarchy_level in rows:
        _get_or_create(
            session,
            IssueType,
            name=name,
            defaults={"is_subtask": is_subtask, "hierarchy_level": hierarchy_level},
        )


def seed_issue_link_types(session: Session) -> None:
    rows = [
        ("Blocks", "blocks", "is blocked by"),
        ("Duplicate", "duplicates", "is duplicated by"),
        ("Relates", "relates to", "relates to"),
        ("Causes", "causes", "is caused by"),
    ]
    for name, outward_name, inward_name in rows:
        _get_or_create(
            session,
            IssueLinkType,
            name=name,
            defaults={
                "outward_name": outward_name,
                "inward_name": inward_name,
                "is_system": True,
            },
        )


def seed_default_workflow(session: Session, statuses: dict[str, Status]) -> Workflow:
    workflow, created = _get_or_create(
        session,
        Workflow,
        name="Default Workflow",
        defaults={"initial_status_id": statuses["Open"].id},
    )
    if not created:
        return workflow

    linear = [
        ("Start Progress", "Open", "In Progress"),
        ("Investigate", "In Progress", "Under Investigation"),
        ("Resume Progress", "Under Investigation", "In Progress"),
        ("Move to QA", "Under Investigation", "QA"),
        ("Fail QA", "QA", "In Progress"),
        ("Close", "QA", "Closed"),
    ]
    for name, from_name, to_name in linear:
        session.add(
            WorkflowTransition(
                workflow_id=workflow.id,
                name=name,
                from_status_id=statuses[from_name].id,
                to_status_id=statuses[to_name].id,
            )
        )
    # Global wildcard transition: reopen from any status back to Open.
    session.add(
        WorkflowTransition(
            workflow_id=workflow.id,
            name="Reopen",
            from_status_id=None,
            to_status_id=statuses["Open"].id,
        )
    )
    session.flush()
    return workflow


def seed_default_workflow_scheme(session: Session, workflow: Workflow) -> WorkflowScheme:
    scheme, created = _get_or_create(session, WorkflowScheme, name="Default Scheme")
    if created:
        session.add(
            WorkflowSchemeEntry(
                workflow_scheme_id=scheme.id, issue_type_id=None, workflow_id=workflow.id
            )
        )
        session.flush()
    return scheme


def seed_project_roles(session: Session) -> dict[str, ProjectRole]:
    roles = {}
    for name in ["Administrator", "Developer", "Viewer"]:
        role, _ = _get_or_create(session, ProjectRole, name=name, defaults={"is_system": True})
        roles[name] = role
    return roles


def seed_permissions(session: Session) -> dict[str, Permission]:
    keys = [
        "issue.create",
        "issue.edit",
        "issue.delete",
        "issue.transition",
        "issue.link",
        "comment.create",
        "comment.delete_any",
        "project.admin",
    ]
    permissions = {}
    for key in keys:
        permission, _ = _get_or_create(session, Permission, key=key)
        permissions[key] = permission
    return permissions


def seed_default_permission_scheme(
    session: Session, roles: dict[str, ProjectRole], permissions: dict[str, Permission]
) -> None:
    scheme, created = _get_or_create(session, PermissionScheme, name="Default Scheme")
    if not created:
        return

    admin_keys = list(permissions.keys())
    developer_keys = [
        "issue.create",
        "issue.edit",
        "issue.transition",
        "issue.link",
        "comment.create",
    ]
    grants = [(roles["Administrator"], k) for k in admin_keys] + [
        (roles["Developer"], k) for k in developer_keys
    ]
    for role, key in grants:
        session.add(
            PermissionSchemeGrant(
                permission_scheme_id=scheme.id,
                permission_id=permissions[key].id,
                role_id=role.id,
            )
        )
    session.flush()


def run() -> None:
    session = SessionLocal()
    try:
        statuses = seed_statuses(session)
        seed_priorities(session)
        seed_issue_types(session)
        seed_issue_link_types(session)
        workflow = seed_default_workflow(session, statuses)
        seed_default_workflow_scheme(session, workflow)
        roles = seed_project_roles(session)
        permissions = seed_permissions(session)
        seed_default_permission_scheme(session, roles, permissions)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run()
