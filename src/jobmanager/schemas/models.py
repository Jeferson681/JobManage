"""Pydantic models and shared types for JobManager API.

This module defines the job `Status` enum and the public request/response
models used by the API.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class Status(str, Enum):
    """Enumerates the lifecycle states of a job."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_FINAL = "FAILED_FINAL"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCELED = "CANCELED"


class JobCreate(BaseModel):
    """Request model for creating a new job."""

    job_type: str
    payload: dict
    max_attempts: int = 3


class JobRead(BaseModel):
    """Representation of a stored job returned by the API."""

    job_id: str
    job_type: str
    payload: Any
    status: Status
    attempt: int
    max_attempts: int
    result: Optional[Any] = None
    last_error: Optional[Any] = None
