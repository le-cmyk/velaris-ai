"""Add dynamic client endpoints

Revision ID: 004_client_endpoints
Revises: 003
Create Date: 2026-05-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004_client_endpoints"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_endpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("path", sa.String(255), nullable=False),
        sa.Column("mode", sa.String(50), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workspace_id", "method", "path", name="uq_client_endpoints_workspace_method_path"),
    )
    op.create_index("ix_client_endpoints_workspace_id", "client_endpoints", ["workspace_id"])
    op.create_index("ix_client_endpoints_created_by_id", "client_endpoints", ["created_by_id"])
    op.create_index("ix_client_endpoints_is_active", "client_endpoints", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_client_endpoints_is_active", table_name="client_endpoints")
    op.drop_index("ix_client_endpoints_created_by_id", table_name="client_endpoints")
    op.drop_index("ix_client_endpoints_workspace_id", table_name="client_endpoints")
    op.drop_table("client_endpoints")
