from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(primary_key=True)
    jira_workflow_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    initial_status_id: Mapped[int] = mapped_column(ForeignKey("statuses.id"), nullable=False)

    initial_status = relationship("Status")
    transitions = relationship(
        "WorkflowTransition", back_populates="workflow", cascade="all, delete-orphan"
    )


class WorkflowStatus(Base):
    __tablename__ = "workflow_statuses"
    __table_args__ = (UniqueConstraint("workflow_id", "status_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflows.id"), nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey("statuses.id"), nullable=False)


class WorkflowTransition(Base):
    __tablename__ = "workflow_transitions"
    __table_args__ = (
        UniqueConstraint("workflow_id", "from_status_id", "to_status_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflows.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    # NULL = wildcard "any status" transition (e.g. global "Reopen")
    from_status_id: Mapped[int | None] = mapped_column(ForeignKey("statuses.id"))
    to_status_id: Mapped[int] = mapped_column(ForeignKey("statuses.id"), nullable=False)

    workflow = relationship("Workflow", back_populates="transitions")
    from_status = relationship("Status", foreign_keys=[from_status_id])
    to_status = relationship("Status", foreign_keys=[to_status_id])


class WorkflowScheme(Base):
    __tablename__ = "workflow_schemes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))

    entries = relationship(
        "WorkflowSchemeEntry", back_populates="workflow_scheme", cascade="all, delete-orphan"
    )


class WorkflowSchemeEntry(Base):
    __tablename__ = "workflow_scheme_entries"
    __table_args__ = (UniqueConstraint("workflow_scheme_id", "issue_type_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    workflow_scheme_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_schemes.id"), nullable=False
    )
    # NULL = default workflow for any issue type not otherwise listed in this scheme
    issue_type_id: Mapped[int | None] = mapped_column(ForeignKey("issue_types.id"))
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflows.id"), nullable=False)

    workflow_scheme = relationship("WorkflowScheme", back_populates="entries")
    workflow = relationship("Workflow")
