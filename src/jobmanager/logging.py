import json
import logging
from datetime import datetime, timezone
from typing import Any


def log_event(event: str, **fields: Any) -> None:
    """Emit a structured log event as JSON to the `jobmanager` logger.

    Fields are merged with the base payload which includes timestamp and
    the event name. This is intentionally lightweight to avoid adding
    extra third-party dependencies.
    """
    logger = logging.getLogger("jobmanager")
    payload = {"event": event, "ts": datetime.now(timezone.utc).isoformat()}
    payload.update(fields)
    try:
        logger.info(json.dumps(payload, default=str))
    except Exception:
        # Logging must not raise; swallow errors to avoid impacting runtime.
        logger.info("{}\n".format(payload))
