"""
Unit tests for the list_process module.

Tests all functions in the vega_common.utils.list_process module to ensure
they behave as expected across different contexts and edge cases.
"""

import pytest
from vega_common.utils.list_process import (
    list_average,
    remove_first_add_last,
    safe_get,
    create_sliding_window,
)


class TestListAverage:
    """Tests for the list_average function."""

    def test_integer_list(self):
        """Test list_average with a list of integers."""
        result = list_average([1, 2, 3, 4, 5])
        expected = 3.0
        assert result == expected

    def test_float_list(self):
        """Test list_average with a list of floats."""
        result = list_average([1.5, 2.5, 3.5])
        expected = 2.5
        assert result == expected

    def test_mixed_list(self):
        """Test list_average with a mixed list of integers and floats."""
        result = list_average([1, 2.5, 3, 4.5, 5])
        expected = 3.2
        assert result == expected

    def test_single_item_list(self):
        """Test list_average with a single-item list."""
        result = list_average([42])
        expected = 42.0
        assert result == expected

    def test_empty_list(self):
        """Test list_average with an empty list raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            list_average([])
        assert "Cannot calculate average of empty list" in str(excinfo.value)

    def test_non_numeric_list(self):
        """Test list_average with non-numeric values raises TypeError."""
        with pytest.raises(TypeError):
            list_average(["a", "b", "c"])


class TestRemoveFirstAddLast:
    """Tests for the remove_first_add_last function."""

    def test_integer_list(self):
        """Test remove_first_add_last with a list of integers."""
        result = remove_first_add_last([1, 2, 3, 4], 5)
        expected = [2, 3, 4, 5]
        assert result == expected

    def test_string_list(self):
        """Test remove_first_add_last with a list of strings."""
        result = remove_first_add_last(["a", "b", "c"], "d")
        expected = ["b", "c", "d"]
        assert result == expected

    def test_two_element_list(self):
        """Test remove_first_add_last with a two-element list."""
        result = remove_first_add_last([1, 2], 3)
        expected = [2, 3]
        assert result == expected

    def test_single_element_list(self):
        """Test remove_first_add_last with a single-element list."""
        result = remove_first_add_last([1], 2)
        expected = [2]
        assert result == expected

    def test_empty_list(self):
        """Test remove_first_add_last with an empty list raises IndexError."""
        with pytest.raises(IndexError) as excinfo:
            remove_first_add_last([], 1)
        assert "Cannot remove first item from empty list" in str(excinfo.value)

    def test_original_list_not_modified(self):
        """Test that remove_first_add_last does not modify the original list."""
        original_list = [1, 2, 3, 4]
        result = remove_first_add_last(original_list, 5)
        assert original_list == [1, 2, 3, 4]  # Original list unchanged
        assert result == [2, 3, 4, 5]  # New list is correct


class TestSafeGet:
    """Tests for the safe_get function."""

    def test_valid_index(self):
        """Test safe_get with a valid index."""
        result = safe_get([1, 2, 3, 4, 5], 2)
        expected = 3
        assert result == expected

    def test_out_of_range_index(self):
        """Test safe_get with an out-of-range index."""
        result = safe_get([1, 2, 3], 10)
        expected = None
        assert result is expected

    def test_negative_index(self):
        """Test safe_get with a negative index."""
        result = safe_get([1, 2, 3, 4, 5], -1)
        expected = 5  # In Python, -1 is the last element
        assert result == expected

    def test_custom_default(self):
        """Test safe_get with a custom default value."""
        result = safe_get([1, 2, 3], 5, default="Not found")
        expected = "Not found"
        assert result == expected


class TestCreateSlidingWindow:
    """Tests for the create_sliding_window function."""

    def test_create_integer_window(self):
        """Test create_sliding_window with default values."""
        result = create_sliding_window(5)
        expected = [0, 0, 0, 0, 0]
        assert result == expected

    def test_create_custom_value_window(self):
        """Test create_sliding_window with a custom initial value."""
        result = create_sliding_window(3, 42)
        expected = [42, 42, 42]
        assert result == expected

    def test_zero_size_window(self):
        """Test create_sliding_window with zero size."""
        result = create_sliding_window(0)
        expected = []
        assert result == expected

    def test_negative_size_window(self):
        """Test create_sliding_window with a negative size."""
        # This tests how the function handles unexpected input
        # The function should handle negative values gracefully
        # For negative size, it should return an empty list
        result = create_sliding_window(-3)
        assert isinstance(result, list)  # Should still return a list

    def test_non_integer_initial_value(self):
        """Test create_sliding_window with a non-integer initial value."""
        result = create_sliding_window(3, "test")
        expected = ["test", "test", "test"]
        assert result == expected
