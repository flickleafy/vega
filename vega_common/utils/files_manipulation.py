"""
File manipulation utilities for the Vega project.

This module provides common file operations used across Vega sub-projects.
"""
from typing import List, Optional, Union, TextIO
import os
from contextlib import contextmanager


def read_file(path: str) -> List[str]:
    """
    Read all lines from a file.
    
    Args:
        path (str): The path to the file to read.
        
    Returns:
        List[str]: A list containing all lines from the file.
        
    Raises:
        FileNotFoundError: If the file doesn't exist.
        PermissionError: If the user lacks permission to read the file.
        IOError: For other I/O related errors.
    """
    try:
        with open(path, 'r') as file_obj:
            lines = file_obj.readlines()
        return lines
    except (FileNotFoundError, PermissionError, IOError) as e:
        # Log the error appropriately before re-raising
        print(f"Error reading file {path}: {e}")
        raise


def write_file(path: str, lines: List[str]) -> None:
    """
    Write lines to a file.
    
    Args:
        path (str): The path to the file to write.
        lines (List[str]): The lines to write to the file.
        
    Returns:
        None
        
    Raises:
        PermissionError: If the user lacks permission to write to the file.
        IOError: For other I/O related errors.
    """
    try:
        with open(path, 'w') as file_obj:
            file_obj.writelines(lines)
    except (PermissionError, IOError) as e:
        # Log the error appropriately before re-raising
        print(f"Error writing to file {path}: {e}")
        raise


@contextmanager
def safe_open(path: str, mode: str = 'r') -> TextIO:
    """
    Safely open a file using a context manager.
    
    Args:
        path (str): The path to the file.
        mode (str): The file opening mode (default: 'r').
        
    Yields:
        TextIO: The file object.
        
    Raises:
        FileNotFoundError: If the file doesn't exist (when mode is 'r').
        PermissionError: If the user lacks permission to access the file.
        IOError: For other I/O related errors.
    """
    try:
        file = open(path, mode)
        yield file
    finally:
        if 'file' in locals():
            file.close()


def ensure_directory_exists(path: str) -> None:
    """
    Ensures that the directory for the specified path exists.
    
    Args:
        path (str): The path to check.
        
    Returns:
        None
    """
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)