"""add manual review audit actions

Revision ID: 71633c174a50
Revises: 117cb1f535cf
Create Date: 2026-10-19 21:48:22.395721

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "71633c174a50"
down_revision: str | Sequence[str] | None = "117cb1f535cf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Register the new manual-review audit actions."""

    op.execute("ALTER TYPE audit_action ADD VALUE 'workflow_review_resolved'")

    op.execute("ALTER TYPE audit_action ADD VALUE 'workflow_review_rejected'")

    op.execute(
        "ALTER TYPE audit_action ADD VALUE 'workflow_review_information_requested'"
    )


def downgrade() -> None:
    """PostgreSQL does not support directly removing enum values."""

    raise NotImplementedError(
        "Downgrading audit_action enum values requires a separate database migration."
    )
