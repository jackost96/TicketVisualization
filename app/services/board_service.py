from sqlalchemy.orm import Session

from app.models.board import Board, BoardColumn
from app.models.project import Project
from app.models.status import Status, StatusCategory

_CATEGORY_ORDER = {
    StatusCategory.todo: 0,
    StatusCategory.in_progress: 1,
    StatusCategory.done: 2,
}


def create_board_with_default_columns(
    db: Session, project: Project, name: str = "Kanban Board"
) -> Board:
    """Snapshots every currently-defined status into this board's columns, ordered by category
    then id. This is a point-in-time snapshot, not a live view -- statuses added later won't
    retroactively appear on boards created before them (prototype limitation)."""
    statuses = db.query(Status).all()
    statuses.sort(key=lambda s: (_CATEGORY_ORDER.get(s.category, 99), s.id))

    board = Board(project_id=project.id, name=name)
    db.add(board)
    db.flush()

    for position, s in enumerate(statuses):
        db.add(BoardColumn(board_id=board.id, status_id=s.id, position=position))
    db.flush()
    return board


def list_boards_for_project(db: Session, project: Project) -> list[Board]:
    return db.query(Board).filter(Board.project_id == project.id).order_by(Board.id).all()
