import logging
import os
from logging.handlers import RotatingFileHandler

from config import LOG_FILE, LOG_LEVEL

def setup_logging() -> None:
    """Send all log records to LOG_FILE. Call once, at startup."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    # Start a new file at 5 MB and keep the 3 previous ones (agent.log.1, .2, .3)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s"))

    root = logging.getLogger()
    root.setLevel(LOG_LEVEL)
    root.addHandler(handler)

    # Library loggers are very chatty at DEBUG, and could log request details we don't want on disk
    for name in ("anthropic", "httpx2", "httpcore2"):
        logging.getLogger(name).setLevel(logging.WARNING)

def shorten(value: object, limit: int = 500) -> str:
    """Keep log lines readable when a value (like file content) is long."""
    text = str(value)
    return text if len(text) <= limit else f"{text[:limit]}... ({len(text)} chars)"
