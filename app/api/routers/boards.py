from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.board import Board
from app.models.project import Project
from app.models.user import User
from app.schemas.board import BoardColumnRead, BoardCreate, BoardRead, BoardSummary
from app.schemas.issue import IssueRead
from app.services import board_service, issue_service
from app.services.permission_service import require_permission

router = APIRouter(tags=["boards"])


def _serialize_board(board: Board) -> BoardRead:
    return BoardRead(
        id=board.id,
        project_id=board.project_id,
        name=board.name,
        swimlane_strategy=board.swimlane_strategy,
        columns=[
            BoardColumnRead(
                status_id=c.status_id,
                name=c.status.name,
                category=c.status.category,
                position=c.position,
            )
            for c in board.columns
        ],
    )


def _get_project_or_404(db: Session, key: str) -> Project:
    project = db.query(Project).filter(Project.key == key).one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("/projects/{key}/boards", response_model=list[BoardSummary])
def list_project_boards(
    key: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    project = _get_project_or_404(db, key)
    return board_service.list_boards_for_project(db, project)


@router.post(
    "/projects/{key}/boards", response_model=BoardSummary, status_code=status.HTTP_201_CREATED
)
def create_project_board(
    key: str,
    payload: BoardCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = _get_project_or_404(db, key)
    require_permission(db, user, project.id, "project.admin")
    board = board_service.create_board_with_default_columns(db, project, name=payload.name)
    db.commit()
    db.refresh(board)
    return board


@router.get("/boards/{board_id}", response_model=BoardRead)
def get_board(board_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    board = db.get(Board, board_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    return _serialize_board(board)


@router.get("/boards/{board_id}/issues", response_model=list[IssueRead])
def get_board_issues(
    board_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    board = db.get(Board, board_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    status_ids = {c.status_id for c in board.columns}
    issues = issue_service.list_issues(db, project_key=board.project.key, limit=500)
    issues = [i for i in issues if i.status_id in status_ids]
    return [issue_service.serialize_issue(i) for i in issues]
