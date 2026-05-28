"""add client_data_records table

Revision ID: 002_client_data
Revises: 001_initial
Create Date: 2024-01-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_client_data"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_data_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_client_data_records_workspace_id", "client_data_records", ["workspace_id"], unique=False)
    op.create_index("ix_client_data_records_type", "client_data_records", ["type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_client_data_records_type", table_name="client_data_records")
    op.drop_index("ix_client_data_records_workspace_id", table_name="client_data_records")
    op.drop_table("client_data_records")
