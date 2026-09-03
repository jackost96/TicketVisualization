"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- reference / config tables -----------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jira_account_id", sa.String(128), unique=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("password_hash", sa.String(255)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    # create_type=False: we create/drop this ENUM type explicitly and only once (below / in
    # downgrade()), rather than relying on SQLAlchemy's implicit on-table-create/drop hooks,
    # to avoid a double-create ("type already exists") error.
    status_category = postgresql.ENUM(
        "todo", "in_progress", "done", name="status_category", create_type=False
    )
    status_category.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "statuses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jira_status_id", sa.String(64), unique=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("category", status_category, nullable=False),
        sa.Column("description", sa.String(500)),
    )

    op.create_table(
        "priorities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jira_priority_id", sa.String(64), unique=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "issue_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jira_issue_type_id", sa.String(64), unique=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(500)),
        sa.Column("icon_key", sa.String(100)),
        sa.Column("is_subtask", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("hierarchy_level", sa.SmallInteger(), nullable=False, server_default="0"),
    )

    op.create_table(
        "issue_link_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jira_link_type_id", sa.String(64), unique=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("outward_name", sa.String(100), nullable=False),
        sa.Column("inward_name", sa.String(100), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(500)),
    )

    op.create_table(
        "project_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(500)),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # --- workflow tables -----------------------------------------------------
    op.create_table(
        "workflows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jira_workflow_id", sa.String(64), unique=True),
        sa.Column("name", sa.String(150), nullable=False, unique=True),
        sa.Column("description", sa.String(500)),
        sa.Column(
            "initial_status_id",
            sa.Integer(),
            sa.ForeignKey("statuses.id"),
            nullable=False,
        ),
    )

    op.create_table(
        "workflow_statuses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workflow_id", sa.Integer(), sa.ForeignKey("workflows.id"), nullable=False),
        sa.Column("status_id", sa.Integer(), sa.ForeignKey("statuses.id"), nullable=False),
        sa.UniqueConstraint("workflow_id", "status_id"),
    )

    op.create_table(
        "workflow_transitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workflow_id", sa.Integer(), sa.ForeignKey("workflows.id"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("from_status_id", sa.Integer(), sa.ForeignKey("statuses.id")),
        sa.Column(
            "to_status_id", sa.Integer(), sa.ForeignKey("statuses.id"), nullable=False
        ),
        sa.UniqueConstraint("workflow_id", "from_status_id", "to_status_id"),
    )

    op.create_table(
        "workflow_schemes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False, unique=True),
        sa.Column("description", sa.String(500)),
    )

    op.create_table(
        "workflow_scheme_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "workflow_scheme_id",
            sa.Integer(),
            sa.ForeignKey("workflow_schemes.id"),
            nullable=False,
        ),
        sa.Column("issue_type_id", sa.Integer(), sa.ForeignKey("issue_types.id")),
        sa.Column("workflow_id", sa.Integer(), sa.ForeignKey("workflows.id"), nullable=False),
        sa.UniqueConstraint("workflow_scheme_id", "issue_type_id"),
    )

    op.create_table(
        "permission_schemes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False, unique=True),
    )

    op.create_table(
        "permission_scheme_grants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "permission_scheme_id",
            sa.Integer(),
            sa.ForeignKey("permission_schemes.id"),
            nullable=False,
        ),
        sa.Column(
            "permission_id", sa.Integer(), sa.ForeignKey("permissions.id"), nullable=False
        ),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("project_roles.id"), nullable=False),
    )

    # --- projects --------------------------------------------------------------
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jira_project_id", sa.String(64), unique=True),
        sa.Column("key", sa.String(20), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(2000)),
        sa.Column("lead_user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column(
            "default_workflow_scheme_id", sa.Integer(), sa.ForeignKey("workflow_schemes.id")
        ),
        sa.Column(
            "permission_scheme_id", sa.Integer(), sa.ForeignKey("permission_schemes.id")
        ),
        sa.Column("next_issue_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    op.create_table(
        "project_issue_types",
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), primary_key=True),
        sa.Column(
            "issue_type_id", sa.Integer(), sa.ForeignKey("issue_types.id"), primary_key=True
        ),
    )

    op.create_table(
        "project_role_members",
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), primary_key=True),
        sa.Column(
            "role_id", sa.Integer(), sa.ForeignKey("project_roles.id"), primary_key=True
        ),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True),
    )

    # --- issues and dependents --------------------------------------------------
    op.create_table(
        "issues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jira_issue_id", sa.String(64), unique=True),
        sa.Column("jira_key", sa.String(50), unique=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("issue_number", sa.Integer(), nullable=False),
        sa.Column(
            "issue_type_id", sa.Integer(), sa.ForeignKey("issue_types.id"), nullable=False
        ),
        sa.Column("status_id", sa.Integer(), sa.ForeignKey("statuses.id"), nullable=False),
        sa.Column("workflow_id", sa.Integer(), sa.ForeignKey("workflows.id"), nullable=False),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("reporter_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("assignee_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("priority_id", sa.Integer(), sa.ForeignKey("priorities.id")),
        sa.Column("parent_issue_id", sa.Integer(), sa.ForeignKey("issues.id")),
        sa.Column("resolution", sa.String(100)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("due_date", sa.Date()),
        sa.Column("story_points", sa.Numeric(6, 2)),
        sa.Column(
            "labels",
            postgresql.ARRAY(sa.String(100)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('english', coalesce(summary, '') || ' ' || coalesce(description, ''))",
                persisted=True,
            ),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("project_id", "issue_number"),
    )
    op.create_index("ix_issues_project_id", "issues", ["project_id"])
    op.create_index("ix_issues_status_id", "issues", ["status_id"])
    op.create_index("ix_issues_assignee_id", "issues", ["assignee_id"])
    op.create_index(
        "ix_issues_search_vector", "issues", ["search_vector"], postgresql_using="gin"
    )
    op.create_index("ix_issues_labels", "issues", ["labels"], postgresql_using="gin")

    op.create_table(
        "issue_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issues.id"), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("old_value", sa.Text()),
        sa.Column("new_value", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_issue_history_issue_id", "issue_history", ["issue_id"])

    op.create_table(
        "issue_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jira_link_id", sa.String(64), unique=True),
        sa.Column(
            "link_type_id", sa.Integer(), sa.ForeignKey("issue_link_types.id"), nullable=False
        ),
        sa.Column(
            "source_issue_id", sa.Integer(), sa.ForeignKey("issues.id"), nullable=False
        ),
        sa.Column(
            "target_issue_id", sa.Integer(), sa.ForeignKey("issues.id"), nullable=False
        ),
        sa.UniqueConstraint("link_type_id", "source_issue_id", "target_issue_id"),
        sa.CheckConstraint(
            "source_issue_id <> target_issue_id", name="ck_issue_link_no_self_link"
        ),
    )

    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jira_comment_id", sa.String(64), unique=True),
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issues.id"), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_comments_issue_id", "comments", ["issue_id"])

    op.create_table(
        "custom_fields",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jira_field_id", sa.String(64), unique=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("field_type", sa.String(50), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id")),
    )

    op.create_table(
        "issue_custom_field_values",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issues.id"), nullable=False),
        sa.Column(
            "custom_field_id", sa.Integer(), sa.ForeignKey("custom_fields.id"), nullable=False
        ),
        sa.Column("value_text", sa.Text()),
        sa.Column("value_number", sa.Numeric(20, 4)),
        sa.Column("value_date", sa.Date()),
        sa.Column("value_json", postgresql.JSONB()),
        sa.UniqueConstraint("issue_id", "custom_field_id"),
    )
    op.create_index(
        "ix_issue_custom_field_values_issue_id", "issue_custom_field_values", ["issue_id"]
    )

    op.create_table(
        "jira_id_map",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("jira_id", sa.String(64), nullable=False),
        sa.Column("local_id", sa.Integer(), nullable=False),
        sa.Column(
            "imported_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("entity_type", "jira_id"),
    )


def downgrade() -> None:
    op.drop_table("jira_id_map")
    op.drop_table("issue_custom_field_values")
    op.drop_table("custom_fields")
    op.drop_table("comments")
    op.drop_table("issue_links")
    op.drop_table("issue_history")
    op.drop_index("ix_issues_labels", table_name="issues")
    op.drop_index("ix_issues_search_vector", table_name="issues")
    op.drop_index("ix_issues_assignee_id", table_name="issues")
    op.drop_index("ix_issues_status_id", table_name="issues")
    op.drop_index("ix_issues_project_id", table_name="issues")
    op.drop_table("issues")
    op.drop_table("project_role_members")
    op.drop_table("project_issue_types")
    op.drop_table("projects")
    op.drop_table("permission_scheme_grants")
    op.drop_table("permission_schemes")
    op.drop_table("workflow_scheme_entries")
    op.drop_table("workflow_schemes")
    op.drop_table("workflow_transitions")
    op.drop_table("workflow_statuses")
    op.drop_table("workflows")
    op.drop_table("project_roles")
    op.drop_table("permissions")
    op.drop_table("issue_link_types")
    op.drop_table("issue_types")
    op.drop_table("priorities")
    op.drop_table("statuses")
    postgresql.ENUM(name="status_category").drop(op.get_bind())
    op.drop_table("users")
