"""
Structured JSON logging setup.

Provides a logger that outputs structured JSON logs compatible with
CloudWatch, Splunk, and other log aggregation systems.

Usage:
    logger = get_logger(__name__)
    logger.info("Operation completed", extra={"duration_ms": 150, "applicant_id": "APP-001"})
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger


def get_logger(name: str) -> logging.Logger:
    """
    Get a structured JSON logger.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured Python logger that outputs JSON

    DESIGN:
      - All logs are JSON for parsing by log aggregators
      - Each log includes timestamp, level, message, and extra fields
      - Unstructured logs go to stderr for visibility during development
    """
    logger = logging.getLogger(name)

    # Only configure once
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # JSON formatter for structured logs
    # Note: Using minimal rename_fields to avoid KeyError on missing fields
    json_formatter = jsonlogger.JsonFormatter(
        fmt="%(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )

    # Console handler (stderr) for development
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(json_formatter)

    logger.addHandler(console_handler)

    return logger


__all__ = ["get_logger"]
