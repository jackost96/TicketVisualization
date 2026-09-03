from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._mixins import TimestampMixin


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    jira_project_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    key: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000))
    lead_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    default_workflow_scheme_id: Mapped[int | None] = mapped_column(
        ForeignKey("workflow_schemes.id")
    )
    permission_scheme_id: Mapped[int | None] = mapped_column(ForeignKey("permission_schemes.id"))
    # Seeded from max imported issue number on migration; incremented on every new issue.
    next_issue_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_archived: Mapped[bool] = mapped_column(default=False, nullable=False)

    lead = relationship("User", foreign_keys=[lead_user_id])
    default_workflow_scheme = relationship("WorkflowScheme")
    permission_scheme = relationship("PermissionScheme")


class ProjectIssueType(Base):
    __tablename__ = "project_issue_types"

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    issue_type_id: Mapped[int] = mapped_column(ForeignKey("issue_types.id"), primary_key=True)
