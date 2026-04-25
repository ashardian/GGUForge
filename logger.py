# =============================================================================
# logger.py — GGUForge Persistent Logger
# All events are written to ~/.gguforge/logs/gguforge.log as well as printed
# to the terminal via the ui helpers. Import log() anywhere in the project.
# =============================================================================

import os
import logging
from config import LOG_DIR, LOG_FILE


def _setup_logger() -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("gguforge")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fmt = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


_logger = _setup_logger()


def log(level: str, msg: str):
    """
    level: 'info' | 'warn' | 'error' | 'debug'
    Also prints a short notice so the user knows events are being recorded.
    """
    level = level.lower()
    if level == "info":
        _logger.info(msg)
    elif level in ("warn", "warning"):
        _logger.warning(msg)
    elif level == "error":
        _logger.error(msg)
    else:
        _logger.debug(msg)


def get_log_path() -> str:
    return LOG_FILE
