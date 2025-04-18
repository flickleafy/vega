"""
Sliding window data structure for the Vega project.

This module provides a fixed-size sliding window implementation for tracking 
time-series data such as temperatures, fan speeds, and other metrics that
require historical context.
"""
from typing import List, Union, TypeVar, Generic, Callable, Optional, Any
import statistics
from collections import deque
import itertools  # Import itertools

T = TypeVar('T')  # Generic type for window elements


class SlidingWindow(Generic[T]):
    """
    A fixed-size sliding window data structure.
    
    This class implements a fixed-size sliding window that efficiently manages 
    a collection of values with a maximum size, automatically removing the oldest
    entries when new ones are added beyond the capacity.
    
    Attributes:
        capacity (int): Maximum number of elements the window can hold.
        window (deque): The underlying data structure storing the elements.
        default_value (T, optional): Default value used for initialization.
    """
    
    def __init__(self, capacity: int, default_value: Optional[T] = None):
        """
        Initialize a new sliding window with the specified capacity.
        
        Args:
            capacity (int): Maximum number of elements the window can hold.
            default_value (T, optional): Default value to pre-fill the window.
                If provided, the window will be initialized with this value
                repeated to fill the capacity. Defaults to None (empty window).
        
        Raises:
            ValueError: If capacity is less than or equal to zero.
        """
        if capacity <= 0:
            raise ValueError("Sliding window capacity must be greater than zero")
        
        self.capacity = capacity
        self.window = deque(maxlen=capacity)
        
        # Pre-fill with default value if provided
        if default_value is not None:
            for _ in range(capacity):
                self.window.append(default_value)
    
    def add(self, value: T) -> None:
        """
        Add a new value to the sliding window.
        
        If the window is at capacity, the oldest value will be removed.
        
        Args:
            value (T): The value to add to the window.
        """
        self.window.append(value)
    
    def get_values(self) -> List[T]:
        """
        Get all values currently in the window.
        
        Returns:
            List[T]: A list containing all values in the window, ordered from oldest to newest.
        """
        return list(self.window)
    
    def clear(self) -> None:
        """Clear all values from the window."""
        self.window.clear()
    
    def is_empty(self) -> bool:
        """
        Check if the window is empty.
        
        Returns:
            bool: True if the window contains no values, False otherwise.
        """
        return len(self.window) == 0
    
    def is_full(self) -> bool:
        """
        Check if the window is at full capacity.
        
        Returns:
            bool: True if the window contains the maximum number of values, False otherwise.
        """
        return len(self.window) == self.capacity
    
    def get_size(self) -> int:
        """
        Get the current number of values in the window.
        
        Returns:
            int: The number of values currently in the sliding window.
        """
        return len(self.window)
    
    def get_capacity(self) -> int:
        """
        Get the maximum capacity of the window.
        
        Returns:
            int: The maximum number of values the window can hold.
        """
        return self.capacity
    
    def get_newest(self) -> Optional[T]:
        """
        Get the most recently added value.
        
        Returns:
            T or None: The newest value in the window, or None if the window is empty.
        """
        if self.is_empty():
            return None
        return self.window[-1]
    
    def get_oldest(self) -> Optional[T]:
        """
        Get the oldest value in the window.
        
        Returns:
            T or None: The oldest value in the window, or None if the window is empty.
        """
        if self.is_empty():
            return None
        return self.window[0]
    
    def __len__(self) -> int:
        """
        Get the current size of the window.
        
        Returns:
            int: The number of values currently in the sliding window.
        """
        return len(self.window)
    
    def __iter__(self):
        """
        Make the window iterable.
        
        Returns:
            iterator: An iterator over the window values.
        """
        return iter(self.window)


class NumericSlidingWindow(SlidingWindow[Union[int, float]]):
    """
    A sliding window specialized for numeric data with statistical functions.
    
    This class extends the basic SlidingWindow to provide statistical operations
    like average, min, max, and other numeric aggregations that are commonly
    needed when tracking temperature, load, or other numeric time-series data.
    """
    
    def fill(self, value: Union[int, float]) -> None:
        """
        Fill the window with the given value if it is currently empty.
        
        This method efficiently populates the entire window capacity with the
        specified value, but only if the window contains no elements.
        If the window is not empty, this method does nothing.
        
        Args:
            value (Union[int, float]): The numeric value to fill the window with.
        """
        # O(C) where C is the capacity, but potentially faster than N appends
        if self.is_empty():
            self.window.extend(itertools.repeat(value, self.capacity))

    def get_average(self) -> float:
        """
        Calculate the average of all values in the window.
        
        Returns:
            float: The mean of all values, or 0.0 if the window is empty.
        """
        if self.is_empty():
            return 0.0
        return statistics.mean(self.window)
    
    def get_median(self) -> float:
        """
        Calculate the median of all values in the window.
        
        Returns:
            float: The median of all values, or 0.0 if the window is empty.
        """
        if self.is_empty():
            return 0.0
        return statistics.median(self.window)
    
    def get_max(self) -> Union[int, float]:
        """
        Get the maximum value in the window.
        
        Returns:
            int or float: The maximum value, or 0 if the window is empty.
        """
        if self.is_empty():
            return 0
        return max(self.window)
    
    def get_min(self) -> Union[int, float]:
        """
        Get the minimum value in the window.
        
        Returns:
            int or float: The minimum value, or 0 if the window is empty.
        """
        if self.is_empty():
            return 0
        return min(self.window)
    
    def get_sum(self) -> Union[int, float]:
        """
        Calculate the sum of all values in the window.
        
        Returns:
            int or float: The sum of all values, or 0 if the window is empty.
        """
        if self.is_empty():
            return 0
        return sum(self.window)
    
    def get_standard_deviation(self) -> float:
        """
        Calculate the sample standard deviation of values in the window.
        
        Returns:
            float: The standard deviation, or 0.0 if the window has fewer than 2 values.
        """
        if len(self.window) < 2:
            return 0.0
        try:
            return statistics.stdev(self.window)
        except statistics.StatisticsError:
            return 0.0
    
    def get_moving_average(self, periods: int) -> float:
        """
        Calculate a simple moving average for the specified number of periods.
        
        Args:
            periods (int): The number of most recent values to include in the average.
                Must be at least 1 and not more than the window size.
        
        Returns:
            float: The average of the most recent 'periods' values, or 0.0 if no values.
            
        Raises:
            ValueError: If periods is less than 1.
        """
        if periods < 1:
            raise ValueError("Periods must be at least 1")
            
        if self.is_empty():
            return 0.0
        
        # Use only the most recent 'periods' values (or all if fewer available)
        actual_periods = min(periods, len(self.window))
        recent_values = list(self.window)[-actual_periods:]
        return sum(recent_values) / actual_periods
    
    def get_weighted_average(self, weights: Optional[List[float]] = None) -> float:
        """
        Calculate a weighted average of values in the window.
        
        Args:
            weights (List[float], optional): The weight for each value, from oldest to newest.
                If None, uses exponential weights favoring newer values. Defaults to None.
                
        Returns:
            float: The weighted average, or 0.0 if the window is empty.
        """
        if self.is_empty():
            return 0.0
        
        # If no weights specified, create exponential weights favoring newer values
        if weights is None:
            weights = [2 ** i for i in range(len(self.window))]
        
        # Ensure weights match the window size
        effective_weights = weights[-len(self.window):] if len(weights) > len(self.window) else weights
        
        # If weights are too few, pad with the last weight
        if len(effective_weights) < len(self.window):
            effective_weights = [effective_weights[0]] * (len(self.window) - len(effective_weights)) + effective_weights
        
        # Calculate weighted sum and sum of weights
        weighted_sum = sum(val * wt for val, wt in zip(self.window, effective_weights))
        sum_of_weights = sum(effective_weights)
        
        return weighted_sum / sum_of_weights if sum_of_weights > 0 else 0.0
    
    def get_trend(self) -> float:
        """
        Calculate a simple trend indicator (positive = rising, negative = falling).
        
        The trend is calculated as the average of the second half minus
        the average of the first half, normalized by the overall average.
        
        Returns:
            float: A value indicating the trend direction and magnitude.
                Positive values indicate an upward trend, negative values a downward trend.
                Returns 0.0 if fewer than 2 values are in the window.
        """
        if len(self.window) < 2:
            return 0.0
            
        # Split the window into two halves
        midpoint = len(self.window) // 2
        first_half = list(self.window)[:midpoint]
        second_half = list(self.window)[midpoint:]
        
        # Calculate averages
        first_avg = sum(first_half) / len(first_half) if first_half else 0
        second_avg = sum(second_half) / len(second_half) if second_half else 0
        overall_avg = self.get_average()
        
        # For mixed positive/negative values where average might be close to zero
        # or when all values are zero, return the raw difference instead of normalized
        if abs(overall_avg) < 0.001:
            return second_avg - first_avg
        
        # Calculate normalized trend
        return (second_avg - first_avg) / overall_avg