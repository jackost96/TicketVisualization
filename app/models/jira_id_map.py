from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JiraIdMap(Base):
    """Migration-only table: resolves Jira ids/keys to local primary keys during ETL,
    and doubles as an audit log of the import run. Not read by the app at runtime."""

    __tablename__ = "jira_id_map"
    __table_args__ = (UniqueConstraint("entity_type", "jira_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    jira_id: Mapped[str] = mapped_column(String(64), nullable=False)
    local_id: Mapped[int] = mapped_column(nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
