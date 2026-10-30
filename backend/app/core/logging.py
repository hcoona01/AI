import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """Structured JSON formatter for production and observable environments."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra") and isinstance(record.extra, dict):  # type: ignore[attr-defined]
            log_data.update(record.extra)  # type: ignore[attr-defined]
        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO", environment: str = "development") -> None:
    """Configure application-wide structured logging."""
    logger = logging.getLogger()
    logger.setLevel(log_level.upper())

    # Remove existing handlers
    while logger.handlers:
        logger.handlers.pop()

    handler = logging.StreamHandler(sys.stdout)
    if environment.lower() == "production":
        handler.setFormatter(JSONFormatter())
    else:
        # Development readable structured format
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
    logger.addHandler(handler)
    logging.getLogger("uvicorn.access").handlers = [handler]
