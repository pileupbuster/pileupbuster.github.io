"""
Utility functions for Pileup Buster backend
"""

from datetime import datetime, timezone
from typing import str


def get_current_timestamp() -> str:
    """
    Get current timestamp with timezone information in ISO format
    Returns UTC timezone-aware timestamp as string
    """
    return datetime.now(timezone.utc).isoformat()


def get_current_datetime() -> datetime:
    """
    Get current datetime with timezone information
    Returns UTC timezone-aware datetime object
    """
    return datetime.now(timezone.utc)


def parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse timestamp string to timezone-aware datetime object
    Handles both timezone-aware and naive timestamps
    """
    try:
        # First try to parse as timezone-aware
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except ValueError:
        try:
            # If that fails, parse as naive and assume UTC
            dt = datetime.fromisoformat(timestamp_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            # If all parsing fails, return current time
            return get_current_datetime()
