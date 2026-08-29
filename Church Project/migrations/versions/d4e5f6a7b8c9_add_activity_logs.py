"""Add activity logs

Revision ID: d4e5f6a7b8c9
Revises: c1a9d7b4e221
Create Date: 2026-08-20 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d4e5f6a7b8c9"
down_revision = "c1a9d7b4e221"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("endpoint", sa.String(length=200), nullable=True),
        sa.Column("section", sa.String(length=50), nullable=False),
        sa.Column("action_label", sa.String(length=255), nullable=False),
        sa.Column("request_summary", sa.String(length=255), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("visitor_key", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("referrer", sa.String(length=500), nullable=True),
        sa.Column("user_id", sa.Uuid(as_uuid=False), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("activity_logs")
