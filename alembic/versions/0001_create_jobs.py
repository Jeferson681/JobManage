"""Create jobs table.

Revision ID: 0001_create_jobs
Revises:
Create Date: 2026-02-10 00:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_create_jobs"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the `jobs` table and idempotency index."""
    op.execute(
        """
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    idempotency_key TEXT,
    status TEXT NOT NULL,
    attempt INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    next_run_at TEXT,
    locked_until TEXT,
    worker_id TEXT,
    result TEXT,
    last_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_idempotency ON jobs (idempotency_key);
"""
    )


def downgrade() -> None:
    """Drop the `jobs` table and associated index."""
    op.execute("DROP INDEX IF EXISTS idx_jobs_idempotency")
    op.execute("DROP TABLE IF EXISTS jobs")
