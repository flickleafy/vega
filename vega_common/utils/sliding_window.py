"""
Sliding window data structure for the Vega project.

This module provides a fixed-size sliding window implementation for tracking
time-series data such as temperatures, fan speeds, and other metrics that
require historical context.
"""

from typing import List, Tuple, Union, TypeVar, Generic, Callable, Optional, Any
import statistics
from collections import deque
import itertools
import math  # Add math import

T = TypeVar("T")  # Generic type for window elements


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
    A sliding window specialized for numeric data with optimized statistical functions.

    This class extends the basic SlidingWindow to provide statistical operations
    like average, min, max, and standard deviation with O(1) retrieval complexity
    by maintaining aggregates incrementally.

    Include numeric aggregations that are commonly needed when tracking temperature,
    load, or other numeric time-series data.
    """

    def __init__(self, capacity: int, default_value: Optional[Union[int, float]] = None):
        """
        Initialize a new numeric sliding window.

        Args:
            capacity (int): Maximum number of elements the window can hold.
            default_value (Union[int, float], optional): Default value to pre-fill.

        Complexity: O(C) if default_value is provided, O(1) otherwise.
        """
        # Initialize base class empty first
        super().__init__(capacity, default_value=None)
        self._current_sum: Union[int, float] = 0
        self._current_sum_sq: Union[int, float] = 0  # For standard deviation

        # Deques to maintain min/max in O(1) amortized time per update
        # Store tuples of (value, index) to handle duplicate values and expiry
        self._min_deque: deque[tuple[Union[int, float], int]] = deque()
        self._max_deque: deque[tuple[Union[int, float], int]] = deque()
        # Global index to track element positions for deque expiry
        self._index = 0

        # Pre-fill if default value is provided, using the optimized fill
        if default_value is not None:
            self.fill(default_value)
            # Ensure index is correct after fill
            self._index = self.capacity

    def add(self, value: Union[int, float]) -> None:
        """
        Add a new value, updating aggregates incrementally.

        Complexity: O(1) amortized.
        """
        # Check if window is full *before* adding, to get the oldest value if needed
        is_full = self.is_full()
        oldest_value = None
        if is_full:
            # O(1) access for deque
            oldest_value = self.window[0]

        # Add the new value (deque handles removal of oldest if full)
        # Complexity: O(1)
        super().add(value)

        # --- Update Sum and Sum of Squares ---
        # Complexity: O(1)
        self._current_sum += value
        self._current_sum_sq += value * value
        if is_full and oldest_value is not None:
            self._current_sum -= oldest_value
            self._current_sum_sq -= oldest_value * oldest_value

        # --- Update Min/Max Deques ---
        # Complexity: O(1) amortized
        current_index = self._index

        # Remove elements from the deques that are older than the current window
        # The oldest element's index in the *new* window is current_index - capacity + 1
        window_start_index = current_index - self.capacity + 1
        if self._min_deque and self._min_deque[0][1] < window_start_index:
            self._min_deque.popleft()
        if self._max_deque and self._max_deque[0][1] < window_start_index:
            self._max_deque.popleft()

        # Maintain min deque (remove larger elements from the back)
        while self._min_deque and self._min_deque[-1][0] >= value:
            self._min_deque.pop()
        self._min_deque.append((value, current_index))

        # Maintain max deque (remove smaller elements from the back)
        while self._max_deque and self._max_deque[-1][0] <= value:
            self._max_deque.pop()
        self._max_deque.append((value, current_index))

        # Increment global index *after* processing the current value
        self._index += 1

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
            # Use itertools.repeat for efficiency
            fill_values = list(itertools.repeat(value, self.capacity))
            # Extend the underlying deque directly
            self.window.extend(fill_values)  # O(C)

            # Calculate initial aggregates directly
            self._current_sum = value * self.capacity  # O(1)
            self._current_sum_sq = (value * value) * self.capacity  # O(1)

            # Initialize min/max deques
            self._min_deque.clear()
            self._max_deque.clear()
            # Since all values are the same, only need one entry
            # The index of the last element added is capacity - 1
            if self.capacity > 0:
                self._min_deque.append((value, self.capacity - 1))
                self._max_deque.append((value, self.capacity - 1))
            # Set index correctly after fill
            self._index = self.capacity

    def clear(self) -> None:
        """
        Clear all values and reset aggregates.

        Complexity: O(1).
        """
        super().clear()  # O(1) for deque clear
        self._current_sum = 0
        self._current_sum_sq = 0
        self._min_deque.clear()  # O(1)
        self._max_deque.clear()  # O(1)
        self._index = 0  # Reset index

    def get_average(self) -> float:
        """
        Calculate the average of all values in the window.

        Complexity: O(1).

        Returns:
            float: The mean of all values, or 0.0 if the window is empty.
        """
        n = len(self.window)  # O(1)
        if n == 0:
            return 0.0
        # Ensure float division
        return float(self._current_sum) / n

    def get_median(self) -> float:
        """
        Calculate the median of all values in the window.

        Complexity: O(N log N) due to sorting/selection.
        Optimization requires more complex data structures (e.g., balanced trees).

        Returns:
            float: The median of all values, or 0.0 if the window is empty.
        """
        if self.is_empty():  # O(1)
            return 0.0
        # statistics.median needs a sequence
        # Creating list is O(N), median calculation is typically O(N log N)
        return statistics.median(self.window)

    def get_max(self) -> Union[int, float]:
        """
        Get the maximum value in the window.

        Complexity: O(1).

        Returns:
            int or float: The maximum value, or 0 if the window is empty.
        """
        if self.is_empty():  # O(1)
            # Consistent with previous implementation's default
            return 0
        # The maximum is always at the front of the max_deque
        # O(1) access
        return self._max_deque[0][0]

    def get_min(self) -> Union[int, float]:
        """
        Get the minimum value in the window.

        Complexity: O(1).

        Returns:
            int or float: The minimum value, or 0 if the window is empty.
        """
        if self.is_empty():  # O(1)
            # Consistent with previous implementation's default
            return 0
        # The minimum is always at the front of the min_deque
        # O(1) access
        return self._min_deque[0][0]

    def get_sum(self) -> Union[int, float]:
        """
        Get the sum of all values in the window.

        Complexity: O(1).

        Returns:
            int or float: The sum of all values, or 0 if the window is empty.
        """
        return self._current_sum

    def get_standard_deviation(self) -> float:
        """
        Calculate the sample standard deviation of values in the window.
        Uses the formula: sqrt( (N*sum_sq - sum*sum) / (N*(N-1)) ) for numerical stability.

        Complexity: O(1).

        Returns:
            float: The standard deviation, or 0.0 if the window has fewer than 2 values.
        """
        n = len(self.window)  # O(1)
        if n < 2:  # Standard deviation requires at least 2 points
            return 0.0

        # Use Welford's online algorithm components (sum and sum_sq)
        # Calculate sample variance: (sum_sq - (sum*sum)/N) / (N-1)
        # Or equivalently: (N*sum_sq - sum*sum) / (N*(N-1))
        sum_val = float(self._current_sum)
        sum_sq_val = float(self._current_sum_sq)

        # Ensure non-negative variance due to potential floating point inaccuracies
        numerator = max(0.0, n * sum_sq_val - sum_val * sum_val)
        denominator = n * (n - 1)

        if denominator <= 0:  # Should not happen if n >= 2, but safeguard
            return 0.0

        sample_variance = numerator / denominator
        return math.sqrt(sample_variance)  # O(1)

    def get_moving_average(self, periods: int) -> float:
        """
        Calculate a simple moving average for the specified number of periods.

        Complexity: O(P) where P is the number of periods (P <= N).
        Optimization to O(1) requires maintaining partial sums, adding complexity.

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

        if self.is_empty():  # O(1)
            return 0.0

        # Accessing last 'periods' elements from deque and summing
        n = len(self.window)  # O(1)
        actual_periods = min(periods, n)

        # Slicing a deque creates a new list O(P)
        # Use islice for potentially better memory efficiency if P is large
        recent_values = list(itertools.islice(self.window, n - actual_periods, n))

        # Summing is O(P)
        return sum(recent_values) / actual_periods

    def get_weighted_average(self, weights: Optional[List[float]] = None) -> float:
        """
        Calculate a weighted average of values in the window.

        Complexity: O(N). Incremental updates are complex with sliding weights.

        Args:
            weights (List[float], optional): The weight for each value, from oldest to newest.
                If None, uses exponential weights favoring newer values. Defaults to None.

        Returns:
            float: The weighted average, or 0.0 if the window is empty.
        """
        # Implementation remains the same as before (O(N))
        if self.is_empty():  # O(1)
            return 0.0

        values = list(self.window)  # O(N)
        n = len(values)

        if weights is None:
            # Generate exponential weights favoring newer values
            effective_weights = [2**i for i in range(n)]  # O(N)
        else:
            # Adjust weights list to match current window size
            if len(weights) >= n:
                effective_weights = weights[len(weights) - n :]  # O(N) slice
            else:  # Pad with first weight if too few weights provided
                effective_weights = [weights[0]] * (n - len(weights)) + weights  # O(N)

        # Calculate weighted sum and sum of weights
        weighted_sum = sum(val * wt for val, wt in zip(values, effective_weights))  # O(N)
        sum_of_weights = sum(effective_weights)  # O(N)

        # Avoid division by zero
        return weighted_sum / sum_of_weights if sum_of_weights != 0 else 0.0

    def get_trend(self) -> float:
        """
        Calculate a simple trend indicator (positive = rising, negative = falling).

        Complexity: O(N). Requires accessing and averaging halves of the window.
        Optimization requires more complex tracking of partial sums.

        The trend is calculated as the average of the second half minus
        the average of the first half, normalized by the overall average.

        Returns:
            float: A value indicating the trend direction and magnitude.
                Positive values indicate an upward trend, negative values a downward trend.
                Returns 0.0 if fewer than 2 values are in the window.
        """
        n = len(self.window)  # O(1)
        if n < 2:
            return 0.0

        # Convert deque to list for slicing O(N)
        values = list(self.window)
        midpoint = n // 2

        # Slicing is O(N/2) = O(N)
        first_half = values[:midpoint]
        second_half = values[midpoint:]

        # statistics.mean is O(N/2) = O(N)
        first_avg = statistics.mean(first_half) if first_half else 0
        second_avg = statistics.mean(second_half) if second_half else 0

        # get_average is O(1) now
        overall_avg = self.get_average()

        # Avoid division by zero or near-zero using a small epsilon
        if abs(overall_avg) < 1e-9:
            # Return raw difference if average is effectively zero
            return second_avg - first_avg

        # Calculate normalized trend O(1)
        return (second_avg - first_avg) / overall_avg

    def get_trend_and_rate(self, threshold: float = 0.2) -> Tuple[float, str]:
        """
        Calculate the temperature trend and rate of change based on window data.

        Uses linear regression to determine the slope (rate of change per sample)
        and classifies the trend direction based on the slope.

        Args:
            threshold (float, optional): Threshold below which the trend is considered
                                        "stable". Defaults to 0.2.

        Returns:
            Tuple[float, str]: A tuple containing:
                - The rate of change per sample (measured in units per sample)
                - A string indicating the trend direction: "rising", "falling", or "stable"

        Time complexity: O(N) where N is the current window size.
        """
        n = len(self.window)
        if n < 2:
            return 0.0, "stable"  # Need at least 2 points for a trend

        # Convert window to list for analysis
        values = list(self.window)
        indices = list(range(n))

        # Calculate means (centroids)
        mean_x = sum(indices) / n  # O(N)
        mean_y = sum(values) / n  # O(N)

        # Calculate linear regression slope using least squares method
        # Complexity: O(N) for the sum operations
        numerator = sum((i - mean_x) * (y - mean_y) for i, y in enumerate(values))
        denominator = sum((i - mean_x) ** 2 for i in indices)

        # Avoid division by zero
        if abs(denominator) < 1e-9:
            return 0.0, "stable"

        slope = numerator / denominator

        # Determine trend direction based on slope and threshold
        if abs(slope) < threshold:
            trend = "stable"
        elif slope > 0:
            trend = "rising"
        else:
            trend = "falling"

        return slope, trend
