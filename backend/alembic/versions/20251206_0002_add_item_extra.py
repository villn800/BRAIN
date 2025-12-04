"""Add extra JSON field to items"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20251206_0002"
down_revision = "20251130_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("items", sa.Column("extra", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("items", "extra")
