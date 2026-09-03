from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    ARRAY,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._mixins import TimestampMixin

_SEARCH_VECTOR_EXPR = (
    "to_tsvector('english', coalesce(summary, '') || ' ' || coalesce(description, ''))"
)


class Issue(TimestampMixin, Base):
    __tablename__ = "issues"
    __table_args__ = (UniqueConstraint("project_id", "issue_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    jira_issue_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    jira_key: Mapped[str | None] = mapped_column(String(50), unique=True)

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    issue_number: Mapped[int] = mapped_column(nullable=False)

    issue_type_id: Mapped[int] = mapped_column(ForeignKey("issue_types.id"), nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey("statuses.id"), nullable=False, index=True)
    # Denormalized at creation time via workflow-scheme resolution, so transition
    # validation doesn't need a join through project -> scheme -> entries every request.
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflows.id"), nullable=False)

    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    reporter_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    priority_id: Mapped[int | None] = mapped_column(ForeignKey("priorities.id"))

    # First-class hierarchy field (Epic -> Story -> Subtask), separate from issue_links,
    # matching how Jira itself distinguishes structural parent/child from associative links.
    parent_issue_id: Mapped[int | None] = mapped_column(ForeignKey("issues.id"))

    resolution: Mapped[str | None] = mapped_column(String(100))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_date: Mapped[date | None] = mapped_column(Date)
    story_points: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    labels: Mapped[list[str]] = mapped_column(ARRAY(String(100)), default=list, nullable=False)

    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR, Computed(_SEARCH_VECTOR_EXPR, persisted=True)
    )

    project = relationship("Project")
    issue_type = relationship("IssueType")
    status = relationship("Status")
    workflow = relationship("Workflow")
    reporter = relationship("User", foreign_keys=[reporter_id])
    assignee = relationship("User", foreign_keys=[assignee_id])
    priority = relationship("Priority")
    parent = relationship("Issue", remote_side=[id])


class IssueHistory(Base):
    __tablename__ = "issue_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"), nullable=False, index=True)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    issue = relationship("Issue")
    author = relationship("User")
