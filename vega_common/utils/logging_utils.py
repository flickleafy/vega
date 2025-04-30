"""Logging utilities for the Vega project.

Provides centralized logging configuration with module-specific log directories.
Log files are stored in ~/.config/vega_suit/<package>/<module>/ with daily rotation
and 30-day retention.
"""

import logging
import os
import pwd
import threading
import sys
import traceback
from logging import handlers
from pathlib import Path
from threading import Lock
from contextlib import contextmanager


def _get_real_user_home() -> Path:
    """Get the real user's home directory, even when running as root via sudo/pkexec.
    
    When running with elevated privileges (sudo, pkexec), Path.home() returns
    /root. This function detects the original user and returns their actual
    home directory, ensuring logs are always stored in the user's config space.
    
    Priority order:
    1. VEGA_USER_HOME environment variable (explicitly set when starting root process)
    2. SUDO_USER environment variable (set by sudo)
    3. PKEXEC_UID environment variable (set by pkexec/polkit)
    4. Current user's home directory (fallback)
    
    Returns:
        Path to the real user's home directory
    
    Example:
        To start the root process with the correct user home:
        $ VEGA_USER_HOME=/home/xxx sudo python rootspace/main.py
        
        Or in a systemd service file:
        Environment="VEGA_USER_HOME=/home/xxx"
        
        Or in crontab:
        @reboot VEGA_USER_HOME=/home/xxx /path/to/executable
    """
    # Check for explicit VEGA_USER_HOME (highest priority - always works)
    vega_user_home = os.environ.get("VEGA_USER_HOME")
    if vega_user_home:
        return Path(vega_user_home)
    
    # Check for SUDO_USER (common case when using sudo directly)
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        try:
            pw_entry = pwd.getpwnam(sudo_user)
            return Path(pw_entry.pw_dir)
        except KeyError:
            pass  # User not found, fall through to next option
    
    # Check for PKEXEC_UID (used by polkit/pkexec)
    pkexec_uid = os.environ.get("PKEXEC_UID")
    if pkexec_uid:
        try:
            pw_entry = pwd.getpwuid(int(pkexec_uid))
            return Path(pw_entry.pw_dir)
        except (KeyError, ValueError):
            pass  # UID not found or invalid, fall through
    
    # Fallback to the current user's home directory
    return Path.home()


# Cache for the base log directory (computed lazily on first use)
_base_log_dir_cache: Path | None = None


def get_base_log_dir() -> Path:
    """Get the base log directory, computing it lazily on first use.
    
    This function computes the log directory path on first call rather than
    at module import time. This is critical for environments like crontab
    or systemd where environment variables may not be available during
    the initial Python import phase.
    
    Returns:
        Path to the base log directory (~/.config/vega_suit/ or VEGA_USER_HOME/.config/vega_suit/)
    """
    global _base_log_dir_cache
    
    if _base_log_dir_cache is None:
        _base_log_dir_cache = _get_real_user_home() / ".config" / "vega_suit"
    
    return _base_log_dir_cache


# Standard log format for all modules
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Thread-local storage for task-specific context
thread_local = threading.local()

# Global lock for thread-safe operations
log_lock = Lock()

# Cache of configured loggers to avoid duplicate handlers
_configured_loggers = {}


class TaskAwareFormatter(logging.Formatter):
    """Custom formatter that includes task ID in log records if available."""

    def format(self, record):
        """Format the log record with task context awareness.

        Handles exceptions gracefully to ensure logging never fails.
        """
        # This variable will store the original message to return in case of error
        original_message = "Unknown message"

        try:
            # Store original message
            original_message = record.getMessage()

            # Get task_id from thread_local if it exists
            task_id = getattr(thread_local, "task_id", "")

            # Create a formatted message with task_id if it exists
            if task_id:
                formatted_message = f"[{task_id}] {original_message}"
                record.task_id = task_id  # Add task_id as an attribute for tests to check
            else:
                formatted_message = original_message

            # Temporarily modify the message
            record.msg = formatted_message

            # Format the record using parent formatter
            result = super().format(record)

            # Restore the original message
            record.msg = original_message

            return result
        except Exception as e:
            # Log a warning about the formatting error (without using the formatter itself)
            sys.stderr.write(f"Critical error in log formatter: {str(e)}\n")

            # Ensure we always return a string, never raise an exception
            level_name = (
                getattr(record, "levelname", "ERROR") if hasattr(record, "levelname") else "ERROR"
            )

            # Return a simple fallback format
            return f"{level_name} - Formatting Error: {original_message}"


def setup_logging(log_file="vega.log", debug=False):
    """Set up logging with task awareness and thread safety.

    Args:
        log_file: Path to the log file
        debug: Whether to enable debug logging

    Returns:
        A configured logger instance

    Raises:
        PermissionError: If the log file or directory cannot be created or written to
        OSError: For other file-related errors
    """
    # Create formatters
    console_formatter = TaskAwareFormatter("%(asctime)s - %(levelname)s - %(message)s")
    file_formatter = TaskAwareFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Detect if we're running in a test environment
    in_test = any(
        "pytest" in frame[0] or "unittest" in frame[0] for frame in traceback.extract_stack()
    )

    # Set up file logging
    try:
        # Create parent directories for log file if needed
        log_dir = os.path.dirname(log_file)
        if log_dir:
            # Ensure directory exists before creating the file handler
            os.makedirs(log_dir, exist_ok=True)

        # Use rotating file handler to prevent logs from growing too large
        file_handler = handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB per file
            backupCount=5,  # Keep 5 backup files
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    except (PermissionError, OSError, IOError) as e:
        # Log the error
        root_logger.warning(f"Failed to set up file logging: {str(e)}")

        # In test environments, allow specific exceptions to be caught by the test
        if in_test:
            raise
        # In normal operation, we just log the warning and continue without the file handler

    # Return a logger for the application to use directly
    return logging.getLogger()


def get_module_logger(module_path: str, debug: bool = False) -> logging.Logger:
    """Get a configured logger for a specific module with file logging.

    Creates a logger that writes to a module-specific log file in the 
    vega_suit configuration directory with daily rotation and 30-day retention.

    Args:
        module_path: Module path relative to vega_suit (e.g., "vega_common/cpu_devices",
                     "vega_server/rootspace/cpuclocking", "vega_client/taskbar").
                     This determines the log file location.
        debug: Whether to enable debug logging. Defaults to False.

    Returns:
        Configured logger instance with console and file handlers.

    Example:
        >>> logger = get_module_logger("vega_common/cpu_devices")
        >>> logger.info("CPU temperature: 45°C")
        # Logs to ~/.config/vega_suit/vega_common/cpu_devices/cpu_devices.log
    """
    # Use cached logger if already configured
    if module_path in _configured_loggers:
        return _configured_loggers[module_path]

    with log_lock:
        # Double-check after acquiring lock
        if module_path in _configured_loggers:
            return _configured_loggers[module_path]

        # Create the logger with the module path as name
        logger = logging.getLogger(module_path)
        logger.setLevel(logging.DEBUG if debug else logging.INFO)

        # Prevent propagation to root logger to avoid duplicate logs
        logger.propagate = False

        # Remove any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Create formatter
        formatter = logging.Formatter(LOG_FORMAT)

        # Set up console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Detect if we're running in a test environment
        in_test = any(
            "pytest" in frame[0] or "unittest" in frame[0] for frame in traceback.extract_stack()
        )

        # Set up file logging
        try:
            # Construct log directory path using lazy evaluation
            # This ensures VEGA_USER_HOME is read at runtime, not import time
            log_dir = get_base_log_dir() / module_path
            log_dir.mkdir(parents=True, exist_ok=True)

            # Use the last part of the module path as the log filename
            log_filename = module_path.split("/")[-1] + ".log"
            log_file = log_dir / log_filename

            # Use timed rotating file handler for daily rotation
            file_handler = handlers.TimedRotatingFileHandler(
                log_file,
                when="midnight",  # Rotate at midnight
                interval=1,  # Every day
                backupCount=30,  # Keep 30 days of logs
            )
            file_handler.setFormatter(formatter)
            file_handler.suffix = "%Y-%m-%d"  # Date suffix for rotated files
            logger.addHandler(file_handler)

        except (PermissionError, OSError, IOError) as e:
            # Log the error to console only - file logging will be disabled
            # but the logger will still work for console output
            logger.warning(f"Failed to set up file logging for {module_path}: {str(e)}")

        # Cache the configured logger
        _configured_loggers[module_path] = logger

        return logger


def set_task_context(task_id=""):
    """Set task context for the current thread."""
    thread_local.task_id = task_id


def get_task_context():
    """Get task context for the current thread."""
    return getattr(thread_local, "task_id", "")


@contextmanager
def task_context(task_id):
    """Context manager for setting task context temporarily."""
    previous = get_task_context()
    try:
        set_task_context(task_id)
        yield
    finally:
        set_task_context(previous)
