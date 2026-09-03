from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.db.base import Base


class StatusCategory(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class Status(Base):
    __tablename__ = "statuses"

    id: Mapped[int] = mapped_column(primary_key=True)
    jira_status_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[StatusCategory] = mapped_column(
        Enum(StatusCategory, name="status_category"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(String(500))


class Priority(Base):
    __tablename__ = "priorities"

    id: Mapped[int] = mapped_column(primary_key=True)
    jira_priority_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    rank: Mapped[int] = mapped_column(nullable=False, default=0)
