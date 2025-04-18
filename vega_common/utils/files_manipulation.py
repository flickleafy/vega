"""
File manipulation utilities for the Vega project.

This module provides common file operations used across Vega sub-projects.
"""
from typing import Any, Dict, List, Optional, Union, TextIO
import os
import json
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
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        path (str): The directory path to check/create.
        
    Returns:
        None
        
    Raises:
        OSError: If the directory cannot be created due to permissions or other issues.
    """
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory {path}: {e}")
        raise


def read_json_file(path: str) -> Union[Dict[str, Any], List[Any], None]:
    """
    Read data from a JSON file.

    Args:
        path (str): The path to the JSON file.

    Returns:
        Union[Dict[str, Any], List[Any], None]: The parsed JSON data, or None if an error occurs.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        PermissionError: If the user lacks permission to read the file.
        json.JSONDecodeError: If the file contains invalid JSON.
        IOError: For other I/O related errors.
    """
    try:
        with open(path, 'r') as file_obj:
            data = json.load(file_obj)
        return data
    except (FileNotFoundError, PermissionError, IOError) as e:
        print(f"Error reading JSON file {path}: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from file {path}: {e}")
        raise


def write_json_file(path: str, data: Union[Dict[str, Any], List[Any]], indent: Optional[int] = 4) -> None:
    """
    Write data to a JSON file.

    Args:
        path (str): The path to the JSON file to write.
        data (Union[Dict[str, Any], List[Any]]): The data to serialize and write.
        indent (Optional[int]): The indentation level for pretty-printing (default: 4). Use None for compact output.

    Returns:
        None

    Raises:
        PermissionError: If the user lacks permission to write to the file.
        TypeError: If the data is not JSON serializable.
        IOError: For other I/O related errors.
    """
    try:
        # Ensure the directory exists before writing
        dir_path = os.path.dirname(path)
        if dir_path: # Avoid trying to create directory for files in the root
            ensure_directory_exists(dir_path)
            
        with open(path, 'w') as file_obj:
            json.dump(data, file_obj, indent=indent)
    except (PermissionError, IOError) as e:
        print(f"Error writing JSON to file {path}: {e}")
        raise
    except TypeError as e:
        print(f"Error serializing data to JSON for file {path}: {e}")
        raise