from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class Status(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_FINAL = "FAILED_FINAL"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCELED = "CANCELED"


class JobCreate(BaseModel):
    job_type: str
    payload: dict
    max_attempts: int = 3


class JobRead(BaseModel):
    job_id: str
    job_type: str
    payload: Any
    status: Status
    attempt: int
    max_attempts: int
    result: Optional[Any] = None
    last_error: Optional[Any] = None
