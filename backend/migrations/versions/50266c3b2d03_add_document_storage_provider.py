"""Add document storage provider.

Revision ID: 50266c3b2d03
Revises: 8636cfbbc134
Create Date: 2026-11-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# Alembic revision identifiers.
revision: str = "50266c3b2d03"
down_revision: str | Sequence[str] | None = "8636cfbbc134"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add storage provider information to documents."""

    op.add_column(
        "documents",
        sa.Column(
            "storage_provider",
            sa.String(length=20),
            server_default="local",
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove document storage provider information."""

    op.drop_column("documents", "storage_provider")
