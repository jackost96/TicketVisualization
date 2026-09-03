from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.permission import PermissionScheme, ProjectRole, ProjectRoleMember
from app.models.project import Project
from app.models.user import User
from app.models.workflow import WorkflowScheme
from app.schemas.project import (
    ProjectCreate,
    ProjectRead,
    ProjectRoleMemberCreate,
    ProjectRoleMemberRead,
    ProjectUpdate,
)
from app.services import board_service
from app.services.permission_service import require_permission

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Project).filter(Project.is_archived.is_(False)).order_by(Project.key).all()


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    if db.query(Project).filter(Project.key == payload.key).one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Project key '{payload.key}' already in use"
        )

    default_workflow_scheme = (
        db.query(WorkflowScheme).filter(WorkflowScheme.name == "Default Scheme").one_or_none()
    )
    default_permission_scheme = (
        db.query(PermissionScheme).filter(PermissionScheme.name == "Default Scheme").one_or_none()
    )

    project = Project(
        key=payload.key,
        name=payload.name,
        description=payload.description,
        lead_user_id=payload.lead_user_id,
        default_workflow_scheme_id=default_workflow_scheme.id if default_workflow_scheme else None,
        permission_scheme_id=default_permission_scheme.id if default_permission_scheme else None,
    )
    db.add(project)
    db.flush()

    admin_role = db.query(ProjectRole).filter(ProjectRole.name == "Administrator").one_or_none()
    if admin_role is not None:
        db.add(ProjectRoleMember(project_id=project.id, role_id=admin_role.id, user_id=user.id))

    board_service.create_board_with_default_columns(db, project)

    db.commit()
    db.refresh(project)
    return project


def _get_project_or_404(db: Session, key: str) -> Project:
    project = db.query(Project).filter(Project.key == key).one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("/{key}", response_model=ProjectRead)
def get_project(key: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return _get_project_or_404(db, key)


@router.patch("/{key}", response_model=ProjectRead)
def update_project(
    key: str,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = _get_project_or_404(db, key)
    require_permission(db, user, project.id, "project.admin")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{key}/roles/{role_id}/members", response_model=list[ProjectRoleMemberRead])
def list_role_members(
    key: str,
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project = _get_project_or_404(db, key)
    return (
        db.query(ProjectRoleMember)
        .filter(ProjectRoleMember.project_id == project.id, ProjectRoleMember.role_id == role_id)
        .all()
    )


@router.post(
    "/{key}/roles/{role_id}/members",
    response_model=ProjectRoleMemberRead,
    status_code=status.HTTP_201_CREATED,
)
def add_role_member(
    key: str,
    role_id: int,
    payload: ProjectRoleMemberCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = _get_project_or_404(db, key)
    require_permission(db, user, project.id, "project.admin")
    role = db.get(ProjectRole, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    member = ProjectRoleMember(project_id=project.id, role_id=role_id, user_id=payload.user_id)
    db.add(member)
    db.commit()
    return member


@router.delete("/{key}/roles/{role_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_role_member(
    key: str,
    role_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = _get_project_or_404(db, key)
    require_permission(db, user, project.id, "project.admin")
    member = db.get(ProjectRoleMember, (project.id, role_id, user_id))
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    db.delete(member)
    db.commit()
