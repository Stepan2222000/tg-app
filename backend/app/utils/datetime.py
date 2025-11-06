"""
Datetime helper utilities for consistent timezone handling.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def to_iso8601(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert datetime to ISO 8601 string with explicit UTC timezone suffix.

    Args:
        dt: Datetime object (naive or timezone-aware)

    Returns:
        ISO 8601 string (e.g., 2025-11-05T12:00:00Z) or None if input is None.
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        aware_dt = dt.replace(tzinfo=timezone.utc)
    else:
        aware_dt = dt.astimezone(timezone.utc)

    return aware_dt.isoformat().replace("+00:00", "Z")

