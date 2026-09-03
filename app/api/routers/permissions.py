from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.permission import EffectivePermissions
from app.services.permission_service import effective_permissions

router = APIRouter(prefix="/projects", tags=["permissions"])


@router.get("/{key}/permissions/me", response_model=EffectivePermissions)
def get_my_permissions(
    key: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.key == key).one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    perms = effective_permissions(db, user, project.id)
    return EffectivePermissions(project_id=project.id, permissions=sorted(perms))
