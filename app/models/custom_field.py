from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CustomField(Base):
    __tablename__ = "custom_fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    jira_field_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    # text | number | date | select | multi_select | user
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))

    project = relationship("Project")


class IssueCustomFieldValue(Base):
    __tablename__ = "issue_custom_field_values"
    __table_args__ = (UniqueConstraint("issue_id", "custom_field_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"), nullable=False, index=True)
    custom_field_id: Mapped[int] = mapped_column(ForeignKey("custom_fields.id"), nullable=False)

    value_text: Mapped[str | None] = mapped_column(Text)
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    value_date: Mapped[date | None] = mapped_column(Date)
    value_json: Mapped[dict | list | None] = mapped_column(JSONB)

    issue = relationship("Issue")
    custom_field = relationship("CustomField")
