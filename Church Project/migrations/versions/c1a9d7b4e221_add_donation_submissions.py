"""Add donation submissions

Revision ID: c1a9d7b4e221
Revises: 86d37535c2ea
Create Date: 2026-08-20 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c1a9d7b4e221"
down_revision = "86d37535c2ea"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "donation_submissions",
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("giving_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("is_anonymous", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("donation_submissions")
