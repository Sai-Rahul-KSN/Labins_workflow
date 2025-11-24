"""
Logging setup for BLMID Validator.
Configures file and console loggers.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(
    log_dir: str = "./output/logs",
    process_log: str = "process.log",
    error_log: str = "error.log",
    level: str = "INFO",
) -> None:
    """
    Configure logging for the application.

    Args:
        log_dir: Directory for log files
        process_log: Main process log filename
        error_log: Error log filename
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create log directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Root logger config
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Process log handler (all messages)
    process_log_path = Path(log_dir) / process_log
    process_handler = logging.handlers.RotatingFileHandler(
        process_log_path, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    process_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    process_handler.setFormatter(formatter)
    root_logger.addHandler(process_handler)

    # Error log handler (errors and above)
    error_log_path = Path(log_dir) / error_log
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_path, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    # Console handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    root_logger.info(f"Logging initialized: {log_dir}")
