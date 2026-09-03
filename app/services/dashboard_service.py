from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.dashboard import Dashboard
from app.models.issue import Issue
from app.models.permission import ProjectRoleMember
from app.models.status import Status
from app.models.user import User

DEFAULT_DASHBOARD_NAME = "My Dashboard"


def list_dashboards_for_user(db: Session, user: User) -> list[Dashboard]:
    return db.query(Dashboard).filter(Dashboard.owner_user_id == user.id).order_by(Dashboard.id).all()


def create_dashboard(db: Session, user: User, name: str) -> Dashboard:
    dashboard = Dashboard(owner_user_id=user.id, name=name)
    db.add(dashboard)
    db.flush()
    return dashboard


def get_or_create_home_dashboard(db: Session, user: User) -> Dashboard:
    """Resolves the dashboard the Home nav link should show: the user's favorite if set,
    otherwise their first dashboard (promoted to favorite), otherwise a freshly created
    default one -- Home always resolves to something without a separate onboarding step."""
    if user.favorite_dashboard_id is not None:
        dashboard = db.get(Dashboard, user.favorite_dashboard_id)
        if dashboard is not None:
            return dashboard

    existing = list_dashboards_for_user(db, user)
    if existing:
        dashboard = existing[0]
    else:
        dashboard = create_dashboard(db, user, DEFAULT_DASHBOARD_NAME)

    user.favorite_dashboard_id = dashboard.id
    db.flush()
    return dashboard


def get_status_counts_for_user(db: Session, user: User) -> list[tuple[int, str, str, int]]:
    """Issue counts by status, across every project the user has any role on."""
    project_ids = (
        db.query(ProjectRoleMember.project_id).filter(ProjectRoleMember.user_id == user.id).distinct()
    ).subquery()

    return (
        db.query(Status.id, Status.name, Status.category, func.count(Issue.id).label("count"))
        .join(Issue, Issue.status_id == Status.id)
        .filter(Issue.project_id.in_(db.query(project_ids.c.project_id)))
        .group_by(Status.id, Status.name, Status.category)
        .order_by(Status.id)
        .all()
    )
