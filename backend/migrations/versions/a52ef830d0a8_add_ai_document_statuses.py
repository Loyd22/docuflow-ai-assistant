"""add ai document statuses

Revision ID: a52ef830d0a8
Revises: 26fdc353d05e
Create Date: 2026-09-18 15:09:04.740711
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a52ef830d0a8"
down_revision: str | Sequence[str] | None = "26fdc353d05e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add AI-analysis lifecycle values to document_status."""

    op.execute("ALTER TYPE document_status ADD VALUE IF NOT EXISTS 'ai_processing'")
    op.execute("ALTER TYPE document_status ADD VALUE IF NOT EXISTS 'analyzed'")
    op.execute(
        "ALTER TYPE document_status ADD VALUE IF NOT EXISTS 'ai_processing_failed'"
    )


def downgrade() -> None:
    """PostgreSQL enum values are not removed automatically on downgrade."""
