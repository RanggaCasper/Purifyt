"""
Logging Manager — Purifyt Application
======================================
Centralized logging configuration with:
  - Console output (colorized, concise)
  - File output (detailed, rotated daily, max 30 days)
  - Separate error log file
  - Per-module logger support via `get_logger(__name__)`

Log files are stored in: `logs/`
  - logs/purifyt.log        → All logs (DEBUG+)
  - logs/purifyt_error.log  → Errors only (ERROR+)

Usage:
    from app.config.logging_config import setup_logging, get_logger

    # Call once at startup (in main.py):
    setup_logging()

    # In any module:
    logger = get_logger(__name__)
    logger.info("Something happened")
"""

import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    LOG_DIR = os.path.join(os.path.dirname(sys.executable), "logs")
else:
    LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "logs")
LOG_DIR = os.path.normpath(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "purifyt.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "purifyt_error.log")

# Format: timestamp | level | module:function:line | message
DETAILED_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
)
CONSOLE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ──────────────────────────────────────────────────────────────
# Setup
# ──────────────────────────────────────────────────────────────
def setup_logging(level: str = "DEBUG") -> None:
    """
    Initialize the root logger with console + file handlers.
    Call this once at application startup (before any log calls).

    Args:
        level: Root log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.DEBUG))

    # Prevent duplicate handlers on repeated calls (e.g. hot-reload)
    if root_logger.handlers:
        root_logger.handlers.clear()

    # ── Console handler (INFO+) ──────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(CONSOLE_FORMAT, datefmt=DATE_FORMAT))
    root_logger.addHandler(console_handler)

    # ── File handler: all logs (DEBUG+), rotated daily, keep 30 days ──
    file_handler = TimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(DETAILED_FORMAT, datefmt=DATE_FORMAT))
    root_logger.addHandler(file_handler)

    # ── Error file handler (ERROR+), rotated daily, keep 30 days ──
    error_handler = TimedRotatingFileHandler(
        ERROR_LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(DETAILED_FORMAT, datefmt=DATE_FORMAT))
    root_logger.addHandler(error_handler)

    # ── Silence noisy third-party loggers ─────────────────────
    for noisy in (
        "httpx",
        "httpcore",
        "urllib3",
        "asyncio",
        "sqlalchemy.engine",
        "watchfiles",
        "uvicorn.access",
        "multipart",
    ):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    root_logger.info(
        "Logging initialized — console=INFO, file=DEBUG, error_file=ERROR | log_dir=%s",
        LOG_DIR,
    )


# ──────────────────────────────────────────────────────────────
# Per-module helper
# ──────────────────────────────────────────────────────────────
def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.  Typical usage:
        logger = get_logger(__name__)

    The returned logger inherits the root logger's handlers set up
    by `setup_logging()`.
    """
    return logging.getLogger(name)
