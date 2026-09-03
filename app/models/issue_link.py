from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IssueLinkType(Base):
    __tablename__ = "issue_link_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    jira_link_type_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    outward_name: Mapped[str] = mapped_column(String(100), nullable=False)
    inward_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class IssueLink(Base):
    __tablename__ = "issue_links"
    __table_args__ = (
        UniqueConstraint("link_type_id", "source_issue_id", "target_issue_id"),
        CheckConstraint("source_issue_id <> target_issue_id", name="ck_issue_link_no_self_link"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    jira_link_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    link_type_id: Mapped[int] = mapped_column(ForeignKey("issue_link_types.id"), nullable=False)
    source_issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"), nullable=False)
    target_issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"), nullable=False)

    link_type = relationship("IssueLinkType")
    source_issue = relationship("Issue", foreign_keys=[source_issue_id])
    target_issue = relationship("Issue", foreign_keys=[target_issue_id])
