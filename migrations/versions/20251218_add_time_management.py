"""add_time_management.

Revision ID: a1b2c3d4e5f6
Revises: 2b2f32bb1c9f
Create Date: 2025-12-18

Add time estimation fields to tasks, at_risk_recovered to commitments,
and create task_history table for audit logging.
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "2b2f32bb1c9f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply migration changes."""
    # Add time estimation fields to tasks table
    op.add_column(
        "tasks",
        sa.Column("estimated_hours", sa.Float(), nullable=True),
    )
    op.add_column(
        "tasks",
        sa.Column(
            "actual_hours_category",
            sa.Enum(
                "MUCH_SHORTER",
                "SHORTER",
                "ON_TARGET",
                "LONGER",
                "MUCH_LONGER",
                name="actualhourscategory",
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "tasks",
        sa.Column(
            "estimation_confidence",
            sa.Enum("HIGH", "MEDIUM", "LOW", name="estimationconfidence"),
            nullable=True,
        ),
    )

    # Add at_risk_recovered to commitments table
    op.add_column(
        "commitments",
        sa.Column("at_risk_recovered", sa.Boolean(), nullable=False, server_default="0"),
    )

    # Create task_history table for audit logging
    op.create_table(
        "task_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("commitment_id", sa.Uuid(), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "CREATED",
                "STARTED",
                "COMPLETED",
                "SKIPPED",
                "ABANDONED",
                name="taskeventtype",
            ),
            nullable=False,
        ),
        sa.Column(
            "previous_status",
            sa.Enum("PENDING", "IN_PROGRESS", "COMPLETED", "SKIPPED", name="taskstatus"),
            nullable=True,
        ),
        sa.Column(
            "new_status",
            sa.Enum("PENDING", "IN_PROGRESS", "COMPLETED", "SKIPPED", name="taskstatus"),
            nullable=False,
        ),
        sa.Column("estimated_hours", sa.Float(), nullable=True),
        sa.Column(
            "actual_hours_category",
            sa.Enum(
                "MUCH_SHORTER",
                "SHORTER",
                "ON_TARGET",
                "LONGER",
                "MUCH_LONGER",
                name="actualhourscategory",
            ),
            nullable=True,
        ),
        sa.Column("notes", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Create indexes for efficient querying
    op.create_index("ix_task_history_task_id", "task_history", ["task_id"])
    op.create_index("ix_task_history_commitment_id", "task_history", ["commitment_id"])
    op.create_index("ix_task_history_created_at", "task_history", ["created_at"])


def downgrade() -> None:
    """Revert migration changes."""
    # Drop task_history table and indexes
    op.drop_index("ix_task_history_created_at", "task_history")
    op.drop_index("ix_task_history_commitment_id", "task_history")
    op.drop_index("ix_task_history_task_id", "task_history")
    op.drop_table("task_history")

    # Remove at_risk_recovered from commitments
    op.drop_column("commitments", "at_risk_recovered")

    # Remove time estimation fields from tasks
    op.drop_column("tasks", "estimation_confidence")
    op.drop_column("tasks", "actual_hours_category")
    op.drop_column("tasks", "estimated_hours")

    # Drop enum types
    sa.Enum(name="taskeventtype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="estimationconfidence").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="actualhourscategory").drop(op.get_bind(), checkfirst=True)
