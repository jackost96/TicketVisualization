from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.project import Project


def allocate_issue_number(db: Session, project: Project) -> int:
    """Atomically claims the next issue_number for a project via a single UPDATE...RETURNING,
    so concurrent issue creation in the same project can't allocate the same number twice
    (the UPDATE's row lock serializes concurrent callers)."""
    result = db.execute(
        update(Project)
        .where(Project.id == project.id)
        .values(next_issue_number=Project.next_issue_number + 1)
        .returning(Project.next_issue_number)
    )
    new_next = result.scalar_one()
    return new_next - 1


def format_key(project_key: str, issue_number: int) -> str:
    return f"{project_key}-{issue_number}"


def parse_key(key: str) -> tuple[str, int]:
    project_key, _, number = key.rpartition("-")
    if not project_key or not number.isdigit():
        raise ValueError(f"'{key}' is not a valid issue key (expected PROJECTKEY-123)")
    return project_key, int(number)
