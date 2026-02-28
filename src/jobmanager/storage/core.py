"""Thin compatibility layer re-exporting storage repository helpers.

This module previously contained the SQLite queries directly. To improve
testability and make the data-access surface easier to reason about the
actual SQL helpers were moved to `storage.repository`. Existing imports
that reference `jobmanager.storage.core` continue to work via these
re-exports.
"""

from .repository import (
    init_db,
    create_job,
    find_by_idempotency_key,
    get_job,
    reserve_next,
    update_job,
)

__all__ = [
    "init_db",
    "create_job",
    "find_by_idempotency_key",
    "get_job",
    "reserve_next",
    "update_job",
]
