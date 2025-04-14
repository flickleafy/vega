"""
Datetime utilities for the Vega project.

This module provides common datetime operations used across Vega sub-projects.
"""
from datetime import datetime, timedelta
from typing import Optional, Union


def get_current_time(time_format: str = "%Y-%m-%d %H:%M:%S - ") -> str:
    """
    Get the current time as a formatted string.
    
    Args:
        time_format (str, optional): The time format string. 
                                    Default is "%Y-%m-%d %H:%M:%S - ".
        
    Returns:
        str: The current time as a formatted string.
    """
    return datetime.now().strftime(time_format)


def get_timestamp(as_string: bool = False, time_format: str = "%Y%m%d%H%M%S") -> Union[int, str]:
    """
    Get a timestamp for use in filenames or logs.
    
    Args:
        as_string (bool, optional): Whether to return the timestamp as a string. 
                                 Default is False (returns an integer timestamp).
        time_format (str, optional): The time format string when as_string is True.
                                  Default is "%Y%m%d%H%M%S".
        
    Returns:
        Union[int, str]: The timestamp as an integer or formatted string.
    """
    now = datetime.now()
    if as_string:
        return now.strftime(time_format)
    else:
        return int(now.timestamp())


def format_duration(seconds: int) -> str:
    """
    Format a duration in seconds to a human-readable string.
    
    Args:
        seconds (int): The duration in seconds.
        
    Returns:
        str: A formatted string representing the duration (e.g., "2h 30m 45s").
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{int(hours)}h")
    if minutes > 0 or hours > 0:
        parts.append(f"{int(minutes)}m")
    parts.append(f"{int(seconds)}s")
    
    return " ".join(parts)


def is_older_than(timestamp: Union[int, datetime], seconds: int) -> bool:
    """
    Check if a timestamp is older than the specified number of seconds.
    
    Args:
        timestamp (Union[int, datetime]): The timestamp to check.
        seconds (int): The number of seconds to compare against.
        
    Returns:
        bool: True if the timestamp is older than the specified seconds, False otherwise.
    """
    if isinstance(timestamp, int):
        timestamp = datetime.fromtimestamp(timestamp)
    
    return (datetime.now() - timestamp).total_seconds() > seconds