"""
Unit tests for the sliding_window module.

Tests the functionality of SlidingWindow and NumericSlidingWindow classes 
to ensure they correctly manage data with fixed-size windows.
"""
import pytest
import math
from vega_common.utils.sliding_window import SlidingWindow, NumericSlidingWindow


class TestSlidingWindow:
    """Test the base SlidingWindow class functionality."""
    
    def test_initialization(self):
        """Test window initialization with different parameters."""
        # Test empty window
        window = SlidingWindow(5)
        assert window.get_capacity() == 5
        assert window.get_size() == 0
        assert window.is_empty() is True
        assert window.is_full() is False
        
        # Test pre-filled window
        prefilled = SlidingWindow(3, default_value="test")
        assert prefilled.get_capacity() == 3
        assert prefilled.get_size() == 3
        assert prefilled.is_full() is True
        assert prefilled.get_values() == ["test", "test", "test"]
        
        # Test invalid capacity
        with pytest.raises(ValueError):
            SlidingWindow(0)
        
        with pytest.raises(ValueError):
            SlidingWindow(-5)
    
    def test_add_and_slide(self):
        """Test adding values and automatic sliding behavior."""
        window = SlidingWindow(3)
        
        # Add values up to capacity
        window.add("a")
        assert window.get_values() == ["a"]
        assert window.get_newest() == "a"
        assert window.get_oldest() == "a"
        
        window.add("b")
        assert window.get_values() == ["a", "b"]
        assert window.get_newest() == "b"
        assert window.get_oldest() == "a"
        
        window.add("c")
        assert window.get_values() == ["a", "b", "c"]
        assert window.is_full() is True
        
        # Add beyond capacity - should slide
        window.add("d")
        assert window.get_values() == ["b", "c", "d"]
        assert window.get_newest() == "d"
        assert window.get_oldest() == "b"
    
    def test_clear(self):
        """Test clearing the window."""
        window = SlidingWindow(3, default_value="x")
        assert window.get_size() == 3
        
        window.clear()
        assert window.get_size() == 0
        assert window.is_empty() is True
        assert window.get_values() == []
        assert window.get_newest() is None
        assert window.get_oldest() is None
    
    def test_iteration(self):
        """Test iterating over window values."""
        window = SlidingWindow(3)
        window.add("a")
        window.add("b")
        window.add("c")
        
        values = [x for x in window]
        assert values == ["a", "b", "c"]
    
    def test_len(self):
        """Test the __len__ method."""
        window = SlidingWindow(5)
        assert len(window) == 0
        
        window.add("a")
        window.add("b")
        assert len(window) == 2


class TestNumericSlidingWindow:
    """Test NumericSlidingWindow statistical functions."""
    
    def test_basic_statistics(self):
        """Test basic statistical functions."""
        window = NumericSlidingWindow(5)
        
        # Empty window statistics
        assert window.get_average() == 0.0
        assert window.get_median() == 0.0
        assert window.get_max() == 0
        assert window.get_min() == 0
        assert window.get_sum() == 0
        
        # Add some values
        values = [10, 20, 30, 40, 50]
        for val in values:
            window.add(val)
        
        # Test statistics
        assert window.get_average() == 30.0
        assert window.get_median() == 30.0
        assert window.get_max() == 50
        assert window.get_min() == 10
        assert window.get_sum() == 150
    
    def test_standard_deviation(self):
        """Test standard deviation calculation."""
        window = NumericSlidingWindow(5)
        
        # Empty window
        assert window.get_standard_deviation() == 0.0
        
        # Single value
        window.add(10)
        assert window.get_standard_deviation() == 0.0
        
        # Multiple values
        window.add(20)
        window.add(30)
        std_dev = window.get_standard_deviation()
        assert math.isclose(std_dev, 10.0, abs_tol=0.001)
        
        # Fill window
        window.add(40)
        window.add(50)
        std_dev = window.get_standard_deviation()
        assert math.isclose(std_dev, 15.811, abs_tol=0.001)
    
    def test_moving_average(self):
        """Test moving average calculation."""
        window = NumericSlidingWindow(5)
        
        # Empty window
        assert window.get_moving_average(3) == 0.0
        
        # Add values
        window.add(10)
        window.add(20)
        window.add(30)
        window.add(40)
        window.add(50)
        
        # Test different periods
        assert window.get_moving_average(1) == 50.0
        assert window.get_moving_average(3) == 40.0
        assert window.get_moving_average(5) == 30.0
        
        # Test periods greater than window size
        assert window.get_moving_average(10) == 30.0
        
        # Test invalid periods
        with pytest.raises(ValueError):
            window.get_moving_average(0)
        
        with pytest.raises(ValueError):
            window.get_moving_average(-1)
    
    def test_weighted_average(self):
        """Test weighted average calculation."""
        window = NumericSlidingWindow(3)
        
        # Empty window
        assert window.get_weighted_average() == 0.0
        
        # Add values
        window.add(10)
        window.add(20)
        window.add(30)
        
        # Default exponential weights
        # Weights would be [1, 2, 4] for values [10, 20, 30]
        # Expected: (10*1 + 20*2 + 30*4) / (1+2+4) = (10 + 40 + 120) / 7 = 170/7 ≈ 24.29
        weighted_avg = window.get_weighted_average()
        assert math.isclose(weighted_avg, 24.286, abs_tol=0.001)
        
        # Custom weights
        custom_weights = [0.1, 0.3, 0.6]
        # Expected: (10*0.1 + 20*0.3 + 30*0.6) / (0.1+0.3+0.6) = (1 + 6 + 18) / 1 = 25.0
        weighted_avg = window.get_weighted_average(custom_weights)
        assert math.isclose(weighted_avg, 25.0, abs_tol=0.001)
        
        # Test with insufficient weights (should pad with first weight)
        short_weights = [0.5, 0.5]
        # Expected padding to [0.5, 0.5, 0.5] for values [10, 20, 30]
        # Result: (10*0.5 + 20*0.5 + 30*0.5) / (0.5+0.5+0.5) = 30/1.5 = 20.0
        weighted_avg = window.get_weighted_average(short_weights)
        assert math.isclose(weighted_avg, 20.0, abs_tol=0.001)
        
        # Test with excess weights (should truncate)
        long_weights = [0.1, 0.2, 0.3, 0.4]
        # Should use only [0.2, 0.3, 0.4] for values [10, 20, 30]
        # Result: (10*0.2 + 20*0.3 + 30*0.4) / (0.2+0.3+0.4) = (2 + 6 + 12) / 0.9 = 22.22
        weighted_avg = window.get_weighted_average(long_weights)
        assert math.isclose(weighted_avg, 22.222, abs_tol=0.001)
    
    def test_trend(self):
        """Test trend calculation."""
        window = NumericSlidingWindow(4)
        
        # Empty window
        assert window.get_trend() == 0.0
        
        # Single value
        window.add(10)
        assert window.get_trend() == 0.0
        
        # Rising trend
        window.add(20)
        window.add(30)
        window.add(40)
        # First half avg: (10+20)/2 = 15
        # Second half avg: (30+40)/2 = 35
        # Overall avg: 25
        # Expected: (35-15)/25 = 0.8
        assert math.isclose(window.get_trend(), 0.8, abs_tol=0.001)
        
        # Falling trend
        window.clear()
        window.add(40)
        window.add(30)
        window.add(20)
        window.add(10)
        # Expected: (15-35)/25 = -0.8
        assert math.isclose(window.get_trend(), -0.8, abs_tol=0.001)
        
        # Stable trend
        window.clear()
        window.add(20)
        window.add(20)
        window.add(20)
        window.add(20)
        assert window.get_trend() == 0.0
        
        # Zero average edge case
        window.clear()
        window.add(0)
        window.add(0)
        window.add(0)
        window.add(0)
        assert window.get_trend() == 0.0
        
        # Mixed positive and negative values
        window.clear()
        window.add(-10)
        window.add(-5)
        window.add(5)
        window.add(10)
        # Note: trend will be normalized by overall average of 0
        # This should still work by falling back to raw difference
        assert window.get_trend() > 0  # Should be positive (rising trend)