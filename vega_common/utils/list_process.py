"""
List processing utilities for the Vega project.

This module provides common list operations used across Vega sub-projects.
"""
from typing import List, TypeVar, Union, Any, Optional
import statistics

T = TypeVar('T', int, float)


def list_average(data: List[T]) -> float:
    """
    Calculate the average value of a list of numbers.
    
    Args:
        data (List[T]): A list of numerical values.
        
    Returns:
        float: The average value.
        
    Raises:
        ValueError: If the list is empty.
        TypeError: If the list contains non-numeric values.
    """
    if not data:
        raise ValueError("Cannot calculate average of empty list")
    
    try:
        return statistics.mean(data)
    except (TypeError, ValueError) as e:
        print(f"Error calculating average: {e}")
        raise


def remove_first_add_last(data: List[Any], last_item: Any) -> List[Any]:
    """
    Remove the first item from a list and append a new item to the end.
    Useful for maintaining fixed-size sliding windows of data.
    
    Args:
        data (List[Any]): The input list to modify.
        last_item (Any): The item to append to the end.
        
    Returns:
        List[Any]: The modified list.
        
    Raises:
        IndexError: If the list is empty.
    """
    if not data:
        raise IndexError("Cannot remove first item from empty list")
    
    # Create a new list to avoid modifying the original if called with immutable values
    result = data.copy()
    result.pop(0)
    result.append(last_item)
    return result


def safe_get(data: List[Any], index: int, default: Any = None) -> Any:
    """
    Safely get an item from a list with a default value if the index is out of range.
    
    Args:
        data (List[Any]): The input list.
        index (int): The index to access.
        default (Any, optional): The default value to return if index is out of range.
        
    Returns:
        Any: The item at the specified index or the default value.
    """
    try:
        return data[index]
    except IndexError:
        return default


def create_sliding_window(size: int, initial_value: T = 0) -> List[T]:
    """
    Create a new list of specified size filled with the initial value.
    Useful for creating sliding windows for averaging.
    
    Args:
        size (int): The size of the list to create.
        initial_value (T, optional): The value to fill the list with.
        
    Returns:
        List[T]: A new list of the specified size filled with the initial value.
        If size is zero or negative, returns an empty list.
    """
    if size <= 0:
        return []
    return [initial_value] * size