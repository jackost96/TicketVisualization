from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._mixins import TimestampMixin


class SavedFilter(TimestampMixin, Base):
    __tablename__ = "saved_filters"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    # subset of the GET /issues query params: project, status_id, assignee_id, reporter_id,
    # issue_type_id, q -- applied client-side by spreading into a GET /issues call.
    query: Mapped[dict] = mapped_column(JSONB, nullable=False)

    owner = relationship("User", foreign_keys=[owner_user_id])
