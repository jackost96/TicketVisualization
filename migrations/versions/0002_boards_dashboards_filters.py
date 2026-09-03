"""boards, dashboards, saved filters

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dashboards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_dashboards_owner_user_id", "dashboards", ["owner_user_id"])

    op.create_table(
        "boards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False, server_default="Kanban Board"),
        sa.Column("swimlane_strategy", sa.String(20), nullable=False, server_default="none"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "swimlane_strategy IN ('none', 'assignee')", name="ck_boards_swimlane_strategy"
        ),
    )
    op.create_index("ix_boards_project_id", "boards", ["project_id"])

    op.create_table(
        "board_columns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("board_id", sa.Integer(), sa.ForeignKey("boards.id"), nullable=False),
        sa.Column("status_id", sa.Integer(), sa.ForeignKey("statuses.id"), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.UniqueConstraint("board_id", "status_id"),
    )
    op.create_index("ix_board_columns_board_id", "board_columns", ["board_id"])

    op.create_table(
        "saved_filters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("query", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_saved_filters_owner_user_id", "saved_filters", ["owner_user_id"])

    # Must come after `dashboards` exists. Named constraint matches the use_alter=True hint on
    # the SQLAlchemy model (users <-> dashboards is a genuine FK cycle).
    op.add_column(
        "users",
        sa.Column(
            "favorite_dashboard_id",
            sa.Integer(),
            sa.ForeignKey("dashboards.id", name="fk_users_favorite_dashboard_id"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "favorite_dashboard_id")
    op.drop_index("ix_saved_filters_owner_user_id", table_name="saved_filters")
    op.drop_table("saved_filters")
    op.drop_index("ix_board_columns_board_id", table_name="board_columns")
    op.drop_table("board_columns")
    op.drop_index("ix_boards_project_id", table_name="boards")
    op.drop_table("boards")
    op.drop_index("ix_dashboards_owner_user_id", table_name="dashboards")
    op.drop_table("dashboards")
