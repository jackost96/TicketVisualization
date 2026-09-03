from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.dashboard import Dashboard
from app.models.user import User
from app.schemas.dashboard import DashboardCreate, DashboardRead, DashboardUpdate, StatusCountRead
from app.services import dashboard_service

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


def _serialize(dashboard: Dashboard, user: User) -> DashboardRead:
    return DashboardRead(
        id=dashboard.id,
        owner_user_id=dashboard.owner_user_id,
        name=dashboard.name,
        is_favorite=(dashboard.id == user.favorite_dashboard_id),
    )


@router.get("/home", response_model=DashboardRead)
def get_home_dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    dashboard = dashboard_service.get_or_create_home_dashboard(db, user)
    db.commit()
    db.refresh(user)
    return _serialize(dashboard, user)


@router.get("/panels/status-counts", response_model=list[StatusCountRead])
def get_status_counts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = dashboard_service.get_status_counts_for_user(db, user)
    return [
        StatusCountRead(status_id=r[0], status_name=r[1], category=r[2], count=r[3]) for r in rows
    ]


@router.get("", response_model=list[DashboardRead])
def list_dashboards(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    dashboards = dashboard_service.list_dashboards_for_user(db, user)
    return [_serialize(d, user) for d in dashboards]


@router.post("", response_model=DashboardRead, status_code=status.HTTP_201_CREATED)
def create_dashboard(
    payload: DashboardCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    dashboard = dashboard_service.create_dashboard(db, user, payload.name)
    db.commit()
    db.refresh(dashboard)
    return _serialize(dashboard, user)


def _get_owned_dashboard_or_404(db: Session, user: User, dashboard_id: int) -> Dashboard:
    dashboard = db.get(Dashboard, dashboard_id)
    if dashboard is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    if dashboard.owner_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the dashboard owner")
    return dashboard


@router.get("/{dashboard_id}", response_model=DashboardRead)
def get_dashboard(
    dashboard_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    dashboard = _get_owned_dashboard_or_404(db, user, dashboard_id)
    return _serialize(dashboard, user)


@router.patch("/{dashboard_id}", response_model=DashboardRead)
def rename_dashboard(
    dashboard_id: int,
    payload: DashboardUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    dashboard = _get_owned_dashboard_or_404(db, user, dashboard_id)
    dashboard.name = payload.name
    db.commit()
    db.refresh(dashboard)
    return _serialize(dashboard, user)


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dashboard(
    dashboard_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    dashboard = _get_owned_dashboard_or_404(db, user, dashboard_id)
    if user.favorite_dashboard_id == dashboard.id:
        user.favorite_dashboard_id = None
    db.delete(dashboard)
    db.commit()


@router.post("/{dashboard_id}/favorite", response_model=DashboardRead)
def favorite_dashboard(
    dashboard_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    dashboard = _get_owned_dashboard_or_404(db, user, dashboard_id)
    user.favorite_dashboard_id = dashboard.id
    db.commit()
    db.refresh(dashboard)
    db.refresh(user)
    return _serialize(dashboard, user)
