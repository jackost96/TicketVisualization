from sqlalchemy import Boolean, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IssueType(Base):
    __tablename__ = "issue_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    jira_issue_type_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    icon_key: Mapped[str | None] = mapped_column(String(100))
    is_subtask: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # -1 = subtask, 0 = standard (Story/Task/Bug), 1 = epic, 2+ = initiative
    hierarchy_level: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
