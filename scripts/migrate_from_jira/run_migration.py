"""Orchestrates the Jira -> Postgres migration in the strict load order required to satisfy
FK constraints (see the plan's section 3.2):

  1. reference data (statuses, priorities, issue_types, issue_link_types)
  2. users
  3. projects (+ enabled issue types + project roles/membership)
  4. issue types <- already loaded in phase 1, linked to projects in phase 3
  5. workflows/schemes -- DEGRADED FALLBACK: this prototype does not reconstruct Jira's actual
     per-project workflow scheme (that requires Jira admin-scoped workflow APIs that are often
     unavailable). Every migrated project is instead assigned the single seeded "Default Scheme" /
     "Default Workflow" from app/seeds/seed_defaults.py. Statuses are still migrated faithfully
     (phase 1), so issue.status_id is accurate even though the *workflow graph* governing legal
     transitions is the prototype's default, not Jira's real one.
  6. issues, pass 1 (parent_issue_id left NULL)
  7. issues, pass 2 (backfill parent_issue_id)
  8. comments
  9. issue links
  10. issue history (changelog)
  11. custom fields (definitions once, then per-issue values)
  12. next_issue_number sequence fix-up per project

Every phase upserts (see load/loaders.py docstring), so the whole pipeline is safely re-runnable,
and extract/*.py cache raw Jira JSON under scratch/jira_export/ so iterating on transform/load
logic doesn't require re-hitting the Jira API every run.

Usage:
    python -m scripts.migrate_from_jira.run_migration --project ENG --project OPS
    python -m scripts.migrate_from_jira.run_migration --dry-run   # extract + cache only, no DB writes
"""
import argparse
import sys

from app.db.session import SessionLocal
from app.models.issue_type import IssueType
from app.models.project import Project, ProjectIssueType
from scripts.migrate_from_jira.config import MigrationConfig
from scripts.migrate_from_jira.extract import custom_fields as extract_custom_fields
from scripts.migrate_from_jira.extract import issues as extract_issues
from scripts.migrate_from_jira.extract import projects as extract_projects
from scripts.migrate_from_jira.extract import reference_data as extract_reference_data
from scripts.migrate_from_jira.extract import users as extract_users
from scripts.migrate_from_jira.jira_client import JiraClient
from scripts.migrate_from_jira.load import loaders
from scripts.migrate_from_jira.transform.issue_mapper import map_issue


class MigrationPreconditionError(Exception):
    pass


def _check_preconditions(db) -> None:
    from app.models.permission import PermissionScheme
    from app.models.workflow import WorkflowScheme

    if db.query(WorkflowScheme).filter(WorkflowScheme.name == "Default Scheme").one_or_none() is None:
        raise MigrationPreconditionError(
            "No 'Default Scheme' workflow scheme found. Run "
            "`python -m app.seeds.seed_defaults` against the target database before migrating."
        )
    if db.query(PermissionScheme).filter(PermissionScheme.name == "Default Scheme").one_or_none() is None:
        raise MigrationPreconditionError(
            "No 'Default Scheme' permission scheme found. Run "
            "`python -m app.seeds.seed_defaults` against the target database before migrating."
        )


class MigrationReport:
    def __init__(self):
        self.counts: dict[str, int] = {}
        self.warnings: list[str] = []

    def bump(self, key: str, n: int = 1) -> None:
        self.counts[key] = self.counts.get(key, 0) + n

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def print_summary(self) -> None:
        print("\n=== Migration summary ===")
        for key, count in sorted(self.counts.items()):
            print(f"  {key}: {count}")
        if self.warnings:
            print(f"\n=== Warnings ({len(self.warnings)}) ===")
            for w in self.warnings[:50]:
                print(f"  - {w}")
            if len(self.warnings) > 50:
                print(f"  ... and {len(self.warnings) - 50} more")


def _migrate_project_issues(db, client, config, project, report: MigrationReport) -> None:
    jira_issues = extract_issues.fetch_issues(client, config, project.key)

    # phase 6: insert with parent_issue_id = NULL; stash the mapped dict for later phases
    # so we don't re-fetch/re-map the same issue JSON repeatedly.
    entries = []  # list[(local Issue, raw jira issue dict, mapped dict)]
    for i, ji in enumerate(jira_issues, start=1):
        if "issuetype" not in ji["fields"] or "status" not in ji["fields"]:
            report.warn(f"{ji['key']}: missing issuetype/status fields, skipped")
            continue
        mapped = map_issue(ji)
        issue = loaders.load_issue_pass1(db, project, mapped, issue_number=i)
        entries.append((issue, ji, mapped))
    db.commit()
    report.bump("issues", len(entries))

    # phase 7: backfill parent_issue_id
    for issue, _ji, mapped in entries:
        loaders.backfill_issue_parent(db, issue, mapped["parent_jira_id"])
    db.commit()

    # phase 8: comments
    for issue, ji, mapped in entries:
        comments = mapped["inline_comments"]
        if mapped["inline_comment_total"] > len(comments):
            comments = extract_issues.fetch_comments_for_issue(client, config, ji["key"])["comments"]
        loaders.load_comments_for_issue(db, issue, comments)
        report.bump("comments", len(comments))
    db.commit()

    # phase 9: issue links (needs all issues in this project already inserted; cross-project
    # links resolve too since id_map is global by the time later projects are processed)
    for _issue, ji, _mapped in entries:
        loaders.load_issue_links(db, ji)
    db.commit()
    report.bump("issue_links", sum(len(ji["fields"].get("issuelinks", [])) for _, ji, _ in entries))

    # phase 10: issue history
    for issue, _ji, mapped in entries:
        loaders.load_issue_history(db, issue, mapped["changelog"])
    db.commit()

    # phase 11 (values half): custom field values, now that phase-11 defs are already loaded
    for issue, _ji, mapped in entries:
        if mapped["custom_fields"]:
            loaders.load_custom_field_values(db, issue, mapped["custom_fields"])
    db.commit()

    # phase 12: sequence fix-up
    loaders.fixup_next_issue_number(db, project)
    db.commit()


def run(config: MigrationConfig) -> MigrationReport:
    report = MigrationReport()
    db = SessionLocal()
    # If no Jira credentials are configured, only cached scratch/jira_export/ data can be used
    # (useful for --dry-run iteration on transform/load logic without live Jira access).
    client = JiraClient(config) if config.jira_base_url else None

    try:
        if not config.dry_run:
            _check_preconditions(db)

        # --- phase 1: reference data ---------------------------------------------------
        statuses = extract_reference_data.fetch_statuses(client, config)
        priorities = extract_reference_data.fetch_priorities(client, config)
        issue_types = extract_reference_data.fetch_issue_types(client, config)
        link_types = extract_reference_data.fetch_issue_link_types(client, config)

        if config.dry_run:
            report.bump("statuses (extracted)", len(statuses))
            report.bump("priorities (extracted)", len(priorities))
            report.bump("issue_types (extracted)", len(issue_types))
            report.bump("issue_link_types (extracted)", len(link_types))
            return report

        loaders.load_statuses(db, statuses)
        loaders.load_priorities(db, priorities)
        loaders.load_issue_types(db, issue_types)
        loaders.load_issue_link_types(db, link_types)
        db.commit()
        report.bump("statuses", len(statuses))
        report.bump("priorities", len(priorities))
        report.bump("issue_types", len(issue_types))
        report.bump("issue_link_types", len(link_types))

        all_issue_type_ids = [
            row.id for row in db.query(IssueType.id).all()
        ]

        # --- phase 2: users --------------------------------------------------------------
        jira_users = extract_users.fetch_users(client, config)
        loaders.load_users(db, jira_users)
        db.commit()
        report.bump("users", len(jira_users))

        # --- phase 3: projects -------------------------------------------------------------
        jira_projects = extract_projects.fetch_projects(client, config)
        local_projects: list[Project] = []
        for jp in jira_projects:
            project = loaders.load_project(db, jp)
            local_projects.append(project)

            for issue_type_id in all_issue_type_ids:
                exists = (
                    db.query(ProjectIssueType)
                    .filter_by(project_id=project.id, issue_type_id=issue_type_id)
                    .one_or_none()
                )
                if exists is None:
                    db.add(ProjectIssueType(project_id=project.id, issue_type_id=issue_type_id))

            roles = extract_projects.fetch_project_roles(client, config, jp["key"])
            loaders.load_project_roles(db, project, roles)
        db.commit()
        report.bump("projects", len(jira_projects))

        # --- phase 11 (defs half): custom field definitions, before per-issue values ------
        jira_fields = extract_custom_fields.fetch_custom_fields(client, config)
        loaders.load_custom_field_defs(db, jira_fields)
        db.commit()
        report.bump("custom_field_defs", len(jira_fields))

        # --- phases 6-12: per-project issue data -------------------------------------------
        for project in local_projects:
            _migrate_project_issues(db, client, config, project, report)

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        if client is not None:
            client.close()

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate data from Jira into this ticket system")
    parser.add_argument("--project", action="append", dest="project_keys", default=[])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=100)
    args = parser.parse_args()

    config = MigrationConfig(
        project_keys=args.project_keys, dry_run=args.dry_run, batch_size=args.batch_size
    )
    report = run(config)
    report.print_summary()
    if report.warnings:
        sys.exit(1)


if __name__ == "__main__":
    main()
