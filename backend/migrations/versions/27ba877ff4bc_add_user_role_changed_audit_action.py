"""Add user role changed audit action.

Revision ID: 27ba877ff4bc
Revises: 50266c3b2d03
Create Date: 2026-11-06 02:23:16.303858
"""

from collections.abc import Sequence

from alembic import op

# Alembic migration identifiers.
revision: str = "27ba877ff4bc"
down_revision: str | Sequence[str] | None = "50266c3b2d03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Register the audit action for user role changes."""

    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'user_role_changed'")


def downgrade() -> None:
    """Enum value removal requires a separate database migration."""

    raise NotImplementedError(
        "Removing user_role_changed requires a separate reviewed migration."
    )
