from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.issue_link import IssueLinkType
from app.models.issue_type import IssueType
from app.models.permission import ProjectRole
from app.models.status import Priority, Status
from app.models.user import User
from app.models.workflow import Workflow
from app.schemas.metadata import (
    IssueLinkTypeCreate,
    IssueLinkTypeRead,
    IssueTypeRead,
    PriorityRead,
    ProjectRoleRead,
    StatusRead,
    WorkflowRead,
)

router = APIRouter(tags=["metadata"])


@router.get("/issue-types", response_model=list[IssueTypeRead])
def list_issue_types(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(IssueType).order_by(IssueType.name).all()


@router.get("/statuses", response_model=list[StatusRead])
def list_statuses(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Status).order_by(Status.name).all()


@router.get("/priorities", response_model=list[PriorityRead])
def list_priorities(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Priority).order_by(Priority.rank).all()


@router.get("/workflows", response_model=list[WorkflowRead])
def list_workflows(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Workflow).order_by(Workflow.name).all()


@router.get("/workflows/{workflow_id}", response_model=WorkflowRead)
def get_workflow(
    workflow_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    workflow = db.get(Workflow, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return workflow


@router.get("/project-roles", response_model=list[ProjectRoleRead])
def list_project_roles(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(ProjectRole).order_by(ProjectRole.id).all()


@router.get("/issue-link-types", response_model=list[IssueLinkTypeRead])
def list_issue_link_types(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(IssueLinkType).order_by(IssueLinkType.name).all()


@router.post(
    "/issue-link-types", response_model=IssueLinkTypeRead, status_code=status.HTTP_201_CREATED
)
def create_issue_link_type(
    payload: IssueLinkTypeCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    if db.query(IssueLinkType).filter(IssueLinkType.name == payload.name).one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Link type '{payload.name}' already exists"
        )
    link_type = IssueLinkType(
        name=payload.name,
        outward_name=payload.outward_name,
        inward_name=payload.inward_name,
        is_system=False,
    )
    db.add(link_type)
    db.commit()
    db.refresh(link_type)
    return link_type
