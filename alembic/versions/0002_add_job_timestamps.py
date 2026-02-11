"""Add started_at and finished_at columns.

Revision ID: 0002_add_job_timestamps
Revises: 0001_create_jobs
Create Date: 2026-02-10 00:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_add_job_timestamps"
down_revision = "0001_create_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add timestamp columns used by the worker for job lifecycle tracking."""
    op.execute("ALTER TABLE jobs ADD COLUMN started_at TEXT")
    op.execute("ALTER TABLE jobs ADD COLUMN finished_at TEXT")


def downgrade() -> None:
    """SQLite cannot drop columns; this downgrade is a no-op."""
    # NOTE: In SQLite, dropping columns requires table rebuild. For this
    # scaffold we keep downgrade as a no-op.
    return
