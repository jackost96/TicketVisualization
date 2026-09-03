from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.permission import (
    PermissionScheme,
    PermissionSchemeGrant,
    ProjectRoleMember,
)
from app.models.project import Project
from app.models.user import User

_DEFAULT_SCHEME_NAME = "Default Scheme"


def _resolve_permission_scheme_id(db: Session, project: Project) -> int | None:
    if project.permission_scheme_id is not None:
        return project.permission_scheme_id
    default_scheme = (
        db.query(PermissionScheme).filter(PermissionScheme.name == _DEFAULT_SCHEME_NAME).one_or_none()
    )
    return default_scheme.id if default_scheme else None


def effective_permissions(db: Session, user: User, project_id: int) -> set[str]:
    project = db.get(Project, project_id)
    if project is None:
        return set()
    scheme_id = _resolve_permission_scheme_id(db, project)
    if scheme_id is None:
        return set()

    role_ids = [
        row.role_id
        for row in db.query(ProjectRoleMember).filter(
            ProjectRoleMember.project_id == project_id, ProjectRoleMember.user_id == user.id
        )
    ]
    if not role_ids:
        return set()

    grants = (
        db.query(PermissionSchemeGrant)
        .filter(
            PermissionSchemeGrant.permission_scheme_id == scheme_id,
            PermissionSchemeGrant.role_id.in_(role_ids),
        )
        .all()
    )
    return {grant.permission.key for grant in grants}


def user_has_permission(db: Session, user: User, project_id: int, permission_key: str) -> bool:
    return permission_key in effective_permissions(db, user, project_id)


def require_permission(db: Session, user: User, project_id: int, permission_key: str) -> None:
    if not user_has_permission(db, user, project_id, permission_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required permission '{permission_key}' on this project",
        )


def require_project_permission(permission_key: str):
    """FastAPI dependency factory for routes with a `project_key` path parameter."""

    def dependency(
        project_key: str,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ) -> Project:
        project = db.query(Project).filter(Project.key == project_key).one_or_none()
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        require_permission(db, user, project.id, permission_key)
        return project

    return dependency
