"""Upsert loaders, one function per phase in the migration's load order (see run_migration.py).

Two upsert strategies are used, deliberately:
  - Reference/config tables (statuses, priorities, issue_types, issue_link_types) upsert-merge
    onto the existing row by `name`, backfilling its jira_*_id. This means running
    app/seeds/seed_defaults.py first and then migrating real Jira data does NOT create
    duplicate "Open"/"Bug"/etc rows -- the seeded row becomes the target of the merge.
  - Everything else (users, projects, issues, links, comments, history, custom fields) upserts
    on its own jira_*_id unique column, since there's no pre-seeded local row to merge onto.
"""
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.custom_field import CustomField, IssueCustomFieldValue
from app.models.issue import Issue, IssueHistory
from app.models.issue_link import IssueLink, IssueLinkType
from app.models.issue_type import IssueType
from app.models.permission import ProjectRole, ProjectRoleMember
from app.models.project import Project
from app.models.status import Status, StatusCategory
from app.models.user import User
from app.models.workflow import WorkflowScheme, WorkflowSchemeEntry
from scripts.migrate_from_jira.load import id_map
from scripts.migrate_from_jira.transform.issue_mapper import adf_to_text
from scripts.migrate_from_jira.transform.user_mapper import map_user

_JIRA_STATUS_CATEGORY_MAP = {
    "new": StatusCategory.todo,
    "indeterminate": StatusCategory.in_progress,
    "done": StatusCategory.done,
}


def _parse_jira_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_jira_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _placeholder_user(db: Session) -> User:
    user = db.query(User).filter(User.is_system.is_(True)).one_or_none()
    if user is None:
        user = User(
            email="migration-placeholder@system.invalid",
            display_name="Deleted Jira User",
            is_system=True,
            is_active=False,
        )
        db.add(user)
        db.flush()
    return user


# --- phase 1: reference data --------------------------------------------------------------


def load_statuses(db: Session, jira_statuses: list[dict]) -> None:
    for js in jira_statuses:
        category_key = (js.get("statusCategory") or {}).get("key", "new")
        category = _JIRA_STATUS_CATEGORY_MAP.get(category_key, StatusCategory.todo)
        status = db.query(Status).filter(Status.name == js["name"]).one_or_none()
        if status is None:
            status = Status(name=js["name"], category=category)
            db.add(status)
            db.flush()
        status.jira_status_id = js["id"]
        status.description = js.get("description") or status.description
        id_map.record(db, "status", js["id"], status.id)
    db.flush()


def load_priorities(db: Session, jira_priorities: list[dict]) -> None:
    for rank, jp in enumerate(jira_priorities):
        from app.models.status import Priority

        priority = db.query(Priority).filter(Priority.name == jp["name"]).one_or_none()
        if priority is None:
            priority = Priority(name=jp["name"], rank=rank)
            db.add(priority)
            db.flush()
        priority.jira_priority_id = jp["id"]
        id_map.record(db, "priority", jp["id"], priority.id)
    db.flush()


def load_issue_types(db: Session, jira_issue_types: list[dict]) -> None:
    for jt in jira_issue_types:
        issue_type = db.query(IssueType).filter(IssueType.name == jt["name"]).one_or_none()
        if issue_type is None:
            issue_type = IssueType(
                name=jt["name"],
                is_subtask=jt.get("subtask", False),
                hierarchy_level=jt.get("hierarchyLevel", 0),
            )
            db.add(issue_type)
            db.flush()
        issue_type.jira_issue_type_id = jt["id"]
        issue_type.description = jt.get("description") or issue_type.description
        id_map.record(db, "issue_type", jt["id"], issue_type.id)
    db.flush()


def load_issue_link_types(db: Session, jira_link_types: list[dict]) -> None:
    for jl in jira_link_types:
        link_type = db.query(IssueLinkType).filter(IssueLinkType.name == jl["name"]).one_or_none()
        if link_type is None:
            link_type = IssueLinkType(
                name=jl["name"], outward_name=jl["outward"], inward_name=jl["inward"]
            )
            db.add(link_type)
            db.flush()
        link_type.jira_link_type_id = jl["id"]
        id_map.record(db, "issue_link_type", jl["id"], link_type.id)
    db.flush()


# --- phase 2: users -----------------------------------------------------------------------


def load_users(db: Session, jira_users: list[dict]) -> None:
    for ju in jira_users:
        mapped = map_user(ju)
        user = (
            db.query(User).filter(User.jira_account_id == mapped["jira_account_id"]).one_or_none()
        )
        if user is None:
            user = User(**mapped)
            db.add(user)
            db.flush()
        else:
            for key, value in mapped.items():
                setattr(user, key, value)
        id_map.record(db, "user", mapped["jira_account_id"], user.id)
    db.flush()


# --- phase 3: projects ----------------------------------------------------------------------


def load_project(db: Session, jira_project: dict) -> Project:
    default_scheme = db.query(WorkflowScheme).filter(WorkflowScheme.name == "Default Scheme").one()
    lead_account_id = (jira_project.get("lead") or {}).get("accountId")
    lead_local_id = id_map.get_local_id(db, "user", lead_account_id)

    project = (
        db.query(Project).filter(Project.jira_project_id == jira_project["id"]).one_or_none()
    )
    if project is None:
        project = Project(key=jira_project["key"], name=jira_project["name"])
        db.add(project)
        db.flush()
    project.jira_project_id = jira_project["id"]
    project.name = jira_project["name"]
    project.description = jira_project.get("description")
    project.lead_user_id = lead_local_id
    if project.default_workflow_scheme_id is None:
        project.default_workflow_scheme_id = default_scheme.id
    id_map.record(db, "project", jira_project["id"], project.id)
    db.flush()
    return project


def load_project_roles(db: Session, project: Project, roles_by_name: dict[str, list[str]]) -> None:
    for role_name, account_ids in roles_by_name.items():
        role = db.query(ProjectRole).filter(ProjectRole.name == role_name).one_or_none()
        if role is None:
            role = ProjectRole(name=role_name, is_system=False)
            db.add(role)
            db.flush()
        for account_id in account_ids:
            user_id = id_map.get_local_id(db, "user", account_id)
            if user_id is None:
                continue
            exists = (
                db.query(ProjectRoleMember)
                .filter_by(project_id=project.id, role_id=role.id, user_id=user_id)
                .one_or_none()
            )
            if exists is None:
                db.add(ProjectRoleMember(project_id=project.id, role_id=role.id, user_id=user_id))
    db.flush()


# --- phase 6/7: issues (two-pass: insert, then backfill parent_issue_id) --------------------


def load_issue_pass1(db: Session, project: Project, mapped: dict, issue_number: int) -> Issue:
    """`mapped` is the output of transform.issue_mapper.map_issue() -- computed once by the
    caller (run_migration.py) and reused across the later comments/links/history/custom-field
    phases, rather than re-derived here."""
    placeholder = _placeholder_user(db)

    issue_type_id = id_map.get_local_id(db, "issue_type", mapped["issue_type_jira_id"])
    status_id = id_map.get_local_id(db, "status", mapped["status_jira_id"])
    priority_id = id_map.get_local_id(db, "priority", mapped["priority_jira_id"])
    reporter_id = id_map.get_local_id(db, "user", mapped["reporter_account_id"]) or placeholder.id
    assignee_id = id_map.get_local_id(db, "user", mapped["assignee_account_id"])

    # Degraded-fidelity fallback (see run_migration.py module docstring): every migrated project
    # is assigned our single seeded Default Scheme/Workflow rather than a reconstruction of
    # Jira's real per-project workflow, so we just need that scheme's default (issue_type_id=NULL)
    # entry here.
    default_entry = (
        db.query(WorkflowSchemeEntry)
        .filter(
            WorkflowSchemeEntry.workflow_scheme_id == project.default_workflow_scheme_id,
            WorkflowSchemeEntry.issue_type_id.is_(None),
        )
        .one_or_none()
    )
    workflow = default_entry.workflow if default_entry else None

    issue = db.query(Issue).filter(Issue.jira_issue_id == mapped["jira_issue_id"]).one_or_none()
    if issue is None:
        issue = Issue(project_id=project.id, issue_number=issue_number)
        db.add(issue)

    issue.jira_issue_id = mapped["jira_issue_id"]
    issue.jira_key = mapped["jira_key"]
    issue.issue_type_id = issue_type_id
    issue.status_id = status_id
    issue.workflow_id = workflow.id if workflow else issue.workflow_id
    issue.summary = mapped["summary"]
    issue.description = mapped["description"]
    issue.reporter_id = reporter_id
    issue.assignee_id = assignee_id
    issue.priority_id = priority_id
    issue.resolution = mapped["resolution"]
    issue.resolved_at = _parse_jira_datetime(mapped["resolved_at"])
    issue.due_date = _parse_jira_date(mapped["due_date"])
    issue.labels = mapped["labels"]
    db.flush()

    id_map.record(db, "issue", mapped["jira_issue_id"], issue.id)
    return issue


def backfill_issue_parent(db: Session, issue: Issue, parent_jira_id: str | None) -> None:
    if not parent_jira_id:
        return
    parent_local_id = id_map.get_local_id(db, "issue", parent_jira_id)
    if parent_local_id is not None:
        issue.parent_issue_id = parent_local_id


# --- phase 8: comments -----------------------------------------------------------------------


def load_comments_for_issue(db: Session, issue: Issue, comments: list[dict]) -> None:
    placeholder = _placeholder_user(db)
    for jc in comments:
        author_account_id = (jc.get("author") or {}).get("accountId")
        author_id = id_map.get_local_id(db, "user", author_account_id) or placeholder.id
        comment = db.query(Comment).filter(Comment.jira_comment_id == jc["id"]).one_or_none()
        if comment is None:
            comment = Comment(issue_id=issue.id, jira_comment_id=jc["id"])
            db.add(comment)
        comment.author_id = author_id
        comment.body = adf_to_text(jc.get("body")) or ""
        db.flush()
        id_map.record(db, "comment", jc["id"], comment.id)


# --- phase 9: issue links ---------------------------------------------------------------------


def load_issue_links(db: Session, jira_issue: dict) -> None:
    source_jira_id = jira_issue["id"]
    source_local_id = id_map.get_local_id(db, "issue", source_jira_id)
    if source_local_id is None:
        return
    for jl in jira_issue["fields"].get("issuelinks", []):
        link_type_local_id = id_map.get_local_id(db, "issue_link_type", jl["type"]["id"])
        if link_type_local_id is None:
            continue

        if "outwardIssue" in jl:
            target_local_id = id_map.get_local_id(db, "issue", jl["outwardIssue"]["id"])
            src, tgt = source_local_id, target_local_id
        elif "inwardIssue" in jl:
            target_local_id = id_map.get_local_id(db, "issue", jl["inwardIssue"]["id"])
            src, tgt = target_local_id, source_local_id
        else:
            continue
        if target_local_id is None or src == tgt:
            continue

        exists = (
            db.query(IssueLink)
            .filter_by(link_type_id=link_type_local_id, source_issue_id=src, target_issue_id=tgt)
            .one_or_none()
        )
        if exists is None:
            db.add(
                IssueLink(
                    jira_link_id=jl["id"],
                    link_type_id=link_type_local_id,
                    source_issue_id=src,
                    target_issue_id=tgt,
                )
            )
    db.flush()


# --- phase 10: issue history (changelog) ------------------------------------------------------


def load_issue_history(db: Session, issue: Issue, histories: list[dict]) -> None:
    placeholder = _placeholder_user(db)
    for change in histories:
        author_account_id = (change.get("author") or {}).get("accountId")
        author_id = id_map.get_local_id(db, "user", author_account_id) or placeholder.id
        created_at = _parse_jira_datetime(change.get("created")) or datetime.now(timezone.utc)
        for item in change.get("items", []):
            db.add(
                IssueHistory(
                    issue_id=issue.id,
                    author_id=author_id,
                    field_name=item.get("field", "unknown"),
                    old_value=item.get("fromString"),
                    new_value=item.get("toString"),
                    created_at=created_at,
                )
            )
    db.flush()


# --- phase 11: custom fields --------------------------------------------------------------------


def load_custom_field_defs(db: Session, jira_fields: list[dict]) -> None:
    for jf in jira_fields:
        field = db.query(CustomField).filter(CustomField.jira_field_id == jf["id"]).one_or_none()
        if field is None:
            field = CustomField(jira_field_id=jf["id"], name=jf["name"], field_type="text")
            db.add(field)
        else:
            field.name = jf["name"]
    db.flush()


def load_custom_field_values(db: Session, issue: Issue, custom_fields: dict) -> None:
    for jira_field_id, raw_value in custom_fields.items():
        field = db.query(CustomField).filter(CustomField.jira_field_id == jira_field_id).one_or_none()
        if field is None:
            continue
        existing = (
            db.query(IssueCustomFieldValue)
            .filter_by(issue_id=issue.id, custom_field_id=field.id)
            .one_or_none()
        )
        if existing is None:
            existing = IssueCustomFieldValue(issue_id=issue.id, custom_field_id=field.id)
            db.add(existing)
        if isinstance(raw_value, (dict, list)):
            existing.value_json = raw_value
        elif isinstance(raw_value, (int, float)):
            existing.value_number = raw_value
        else:
            existing.value_text = str(raw_value)
    db.flush()


# --- phase 12: sequence fix-up -------------------------------------------------------------------


def fixup_next_issue_number(db: Session, project: Project) -> None:
    max_number = (
        db.query(Issue.issue_number)
        .filter(Issue.project_id == project.id)
        .order_by(Issue.issue_number.desc())
        .limit(1)
        .scalar()
    )
    project.next_issue_number = (max_number or 0) + 1
    db.flush()
