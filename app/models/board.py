from sqlalchemy import ForeignKey, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._mixins import TimestampMixin


class Board(TimestampMixin, Base):
    __tablename__ = "boards"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False, default="Kanban Board")
    # "none" | "assignee" -- which field cards are additionally grouped by within a column
    swimlane_strategy: Mapped[str] = mapped_column(String(20), nullable=False, default="none")

    project = relationship("Project")
    columns = relationship(
        "BoardColumn", back_populates="board", cascade="all, delete-orphan",
        order_by="BoardColumn.position",
    )


class BoardColumn(Base):
    __tablename__ = "board_columns"
    __table_args__ = (UniqueConstraint("board_id", "status_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id"), nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey("statuses.id"), nullable=False)
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    board = relationship("Board", back_populates="columns")
    status = relationship("Status")
