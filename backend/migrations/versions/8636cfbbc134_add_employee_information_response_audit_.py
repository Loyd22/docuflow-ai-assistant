"""Add employee information response audit action.

Revision ID: 8636cfbbc134
Revises: cc84f2a36249
Create Date: 2026-10-22 00:43:34.611321

"""

from collections.abc import Sequence

from alembic import op

# Alembic migration identifiers.
revision: str = "8636cfbbc134"
down_revision: str | Sequence[str] | None = "cc84f2a36249"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the audit action for employee information responses."""

    op.execute("ALTER TYPE audit_action ADD VALUE 'workflow_information_responded'")


def downgrade() -> None:
    """Removing PostgreSQL enum values requires a separate migration."""

    raise NotImplementedError(
        "Downgrading audit_action enum values requires a separate database migration."
    )
