import logging
import os
from datetime import datetime

from config import LOG_DIR, LOG_LEVEL, LOG_PREVIEW_CHARS

def setup_logging() -> str:
    """Send all log records to a new file for this run. Call once, at startup. Returns the file path."""
    os.makedirs(LOG_DIR, exist_ok=True)

    # One file per run, named by start time, e.g. logs/agent_2026-10-26_07-15-02.log
    log_file = os.path.join(LOG_DIR, f"agent_{datetime.now():%Y-%m-%d_%H-%M-%S}.log")
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s"))

    root = logging.getLogger()
    root.setLevel(LOG_LEVEL)
    root.addHandler(handler)

    # Library loggers are very chatty at DEBUG, and could log request details we don't want on disk
    for name in ("anthropic", "httpx2", "httpcore2"):
        logging.getLogger(name).setLevel(logging.WARNING)

    return log_file

def shorten(value: object, limit: int = LOG_PREVIEW_CHARS) -> str:
    """Keep log lines readable when a value (like file content) is long."""
    text = str(value)
    return text if len(text) <= limit else f"{text[:limit]}... ({len(text)} chars)"
