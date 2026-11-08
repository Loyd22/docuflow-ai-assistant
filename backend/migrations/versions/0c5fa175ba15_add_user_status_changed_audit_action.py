"""add user status changed audit action

Revision ID: 0c5fa175ba15
Revises: 27ba877ff4bc
Create Date: 2026-11-08 18:09:51.035376

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0c5fa175ba15"
down_revision: str | Sequence[str] | None = "27ba877ff4bc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Register the audit action for account status changes."""

    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'user_status_changed'")


def downgrade() -> None:
    """Enum value removal requires a separate reviewed migration."""

    raise NotImplementedError(
        "Removing user_status_changed requires a separate reviewed migration."
    )
