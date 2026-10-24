"""Add workflow reviews.

Revision ID: 117cb1f535cf
Revises: a8be8ba6519c
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "117cb1f535cf"
down_revision: str | Sequence[str] | None = "a8be8ba6519c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Define the PostgreSQL enum used by manual reviews.
review_outcome_enum = postgresql.ENUM(
    "resolved",
    "rejected",
    "information_requested",
    name="review_outcome",
    create_type=False,
)


def upgrade() -> None:
    """Create the workflow review table."""

    # Create the enum before creating the table.
    review_outcome_enum.create(
        op.get_bind(),
        checkfirst=False,
    )

    op.create_table(
        "workflow_reviews",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "workflow_id",
            sa.Integer(),
            sa.ForeignKey("workflows.id"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "outcome",
            review_outcome_enum,
            nullable=False,
        ),
        sa.Column(
            "comment",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_workflow_reviews_workflow_id",
        "workflow_reviews",
        ["workflow_id"],
    )

    op.create_index(
        "ix_workflow_reviews_reviewer_id",
        "workflow_reviews",
        ["reviewer_id"],
    )


def downgrade() -> None:
    """Remove workflow reviews and their enum type."""

    op.drop_index(
        "ix_workflow_reviews_reviewer_id",
        table_name="workflow_reviews",
    )

    op.drop_index(
        "ix_workflow_reviews_workflow_id",
        table_name="workflow_reviews",
    )

    op.drop_table("workflow_reviews")

    # Remove the enum only after the table is removed.
    review_outcome_enum.drop(
        op.get_bind(),
        checkfirst=False,
    )
