from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    jira_account_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    # use_alter=True: users <-> dashboards is a genuine FK cycle (dashboards.owner_user_id -> users.id,
    # users.favorite_dashboard_id -> dashboards.id). This tells SQLAlchemy to emit/drop this specific
    # constraint via a separate ALTER TABLE, which is required for metadata-driven create_all/drop_all
    # (e.g. the test suite) to resolve the cycle -- matches how migration 0002 adds this column too.
    favorite_dashboard_id: Mapped[int | None] = mapped_column(
        ForeignKey("dashboards.id", use_alter=True, name="fk_users_favorite_dashboard_id")
    )
