"""
Subprocess utilities for the Vega project.

This module provides common subprocess operations used across Vega sub-projects.
"""

import subprocess
from typing import List, Union, Optional, Dict, Any, Tuple

from vega_common.utils.logging_utils import get_module_logger

# Setup module-specific logging
logger = get_module_logger("vega_common/utils/sub_process")


def run_cmd(
    cmd: Union[List[str], str],
    shell: bool = True,
    timeout: Optional[int] = None,
    capture_output: bool = True,
) -> str:
    """
    Run a shell command and return its output.

    Args:
        cmd (Union[List[str], str]): The command to run, either as a string or list of strings.
        shell (bool, optional): Whether to run the command through a shell. Default is True.
        timeout (Optional[int], optional): Timeout in seconds. Default is None (no timeout).
        capture_output (bool, optional): Whether to capture and return the command output. Default is True.

    Returns:
        str: The command output (stdout) as a string.

    Raises:
        subprocess.SubprocessError: For subprocess related errors.
        subprocess.TimeoutExpired: If the command times out.
    """
    try:
        if isinstance(cmd, list) and shell:
            # Join the command list for shell execution
            cmd_str = " ".join(cmd)
        else:
            cmd_str = cmd

        result = subprocess.run(
            cmd_str if shell else cmd,
            shell=shell,
            check=True,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            universal_newlines=True,
            timeout=timeout,
        )

        return result.stdout.strip() if capture_output else ""
    except subprocess.CalledProcessError as e:
        # Check if this is a permission error
        if e.stderr and ("permission denied" in e.stderr.lower() or "operation not permitted" in e.stderr.lower()):
            raise PermissionError(f"Insufficient permissions to run command: {cmd_str if shell else cmd}") from e
        # Re-raise the original error for other cases
        raise
    except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
        logger.error(f"Error running command {cmd}: {e}")
        raise


def run_cmd_with_status(cmd: Union[List[str], str], shell: bool = True) -> Tuple[bool, str]:
    """
    Run a shell command and return both its status and output.

    Args:
        cmd (Union[List[str], str]): The command to run.
        shell (bool, optional): Whether to run the command through a shell. Default is True.

    Returns:
        Tuple[bool, str]: A tuple containing (success_status, output_or_error_message)
    """
    try:
        output = run_cmd(cmd, shell)
        return True, output
    except Exception as e:
        return False, str(e)


def run_cmd_sudo(cmd: Union[List[str], str], password: Optional[str] = None) -> str:
    """
    Run a command with sudo privileges.

    Args:
        cmd (Union[List[str], str]): The command to run.
        password (Optional[str], optional): The sudo password. If None, assumes passwordless sudo.

    Returns:
        str: The command output as a string.
    """
    # Prepend sudo to the command if it's not already there
    if isinstance(cmd, list):
        if cmd[0] != "sudo":
            cmd = ["sudo"] + cmd
    else:
        if not cmd.strip().startswith("sudo "):
            cmd = f"sudo {cmd}"

    if password:
        # Use subprocess.Popen to send the password to stdin
        process = subprocess.Popen(
            cmd if isinstance(cmd, list) else cmd.split(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        stdout, stderr = process.communicate(input=password + "\n")
        if process.returncode != 0:
            raise subprocess.SubprocessError(f"Command failed with error: {stderr}")
        return stdout.strip()
    else:
        # Run without password
        return run_cmd(cmd)
