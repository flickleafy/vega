"""
Unit tests for the vectorized color operations in color_utils module.

Tests the new vectorized functions for batch color processing operations.
"""

import pytest
import time
from vega_common.utils.color_utils import rgb_to_hsv, hsv_to_rgb, calculate_color_distance
from vega_common.utils.vectorized_color_utils import (
    normalize_multiple_colors,
    vectorized_rgb_to_hsv,
    vectorized_hsv_to_rgb,
    batch_color_distance,
)


class TestVectorizedColorOperations:
    """Tests for vectorized color operations."""

    def test_normalize_multiple_colors(self):
        """Test normalize_multiple_colors with various inputs."""
        # Test with normal colors
        colors = [[100, 150, 200], [255, 0, 0], [0, 255, 0]]
        normalized = normalize_multiple_colors(colors)
        assert normalized == colors  # Should be unchanged

        # Test with out-of-range values
        colors = [
            [300, 150, 200],  # Red too high
            [-50, 255, 0],  # Red too low
            [0, 300, -10],  # Green too high, blue too low
        ]
        expected = [
            [255, 150, 200],  # Red clamped to 255
            [0, 255, 0],  # Red clamped to 0
            [0, 255, 0],  # Green clamped to 255, blue clamped to 0
        ]
        normalized = normalize_multiple_colors(colors)
        assert normalized == expected

        # Test with invalid colors
        colors = [
            [100, 150, 200],  # Valid color
            [100],  # Invalid (too short)
            [100, 150],  # Invalid (too short)
            [],  # Invalid (empty)
            [100, 150, 200, 255],  # Valid with extra value
        ]
        normalized = normalize_multiple_colors(colors)
        assert len(normalized) == 5
        assert normalized[0] == [100, 150, 200]  # Valid color unchanged
        assert normalized[1] == [100]  # Invalid color unchanged
        assert normalized[2] == [100, 150]  # Invalid color unchanged
        assert normalized[3] == []  # Invalid (empty) unchanged
        assert normalized[4][:3] == [100, 150, 200]  # First 3 values normalized

        # Test with empty list
        assert normalize_multiple_colors([]) == []

    def test_vectorized_rgb_to_hsv(self):
        """Test vectorized_rgb_to_hsv with various valid inputs."""
        # Test with standard colors
        rgb_colors = [[255, 0, 0], [0, 255, 0], [0, 0, 255]]  # Red  # Green  # Blue
        expected_hsv = [
            [0, 100, 100],  # Red in HSV
            [120, 100, 100],  # Green in HSV
            [240, 100, 100],  # Blue in HSV
        ]
        hsv_colors = vectorized_rgb_to_hsv(rgb_colors)

        # Compare each color with a small tolerance for floating point differences
        assert len(hsv_colors) == len(expected_hsv)
        for i in range(len(expected_hsv)):
            assert hsv_colors[i] == pytest.approx(expected_hsv[i], abs=0.5)

    def test_vectorized_rgb_to_hsv_empty_input(self):
        """Test vectorized_rgb_to_hsv with empty input."""
        # Explicitly test the empty list case to ensure coverage
        assert vectorized_rgb_to_hsv([]) == []

    def test_vectorized_rgb_to_hsv_invalid_input(self):
        """Test vectorized_rgb_to_hsv raises error with invalid inputs."""
        invalid_rgb_lists = [
            [[255, 0, 0], [100], [0, 0, 255]],  # Contains short list
            [[255, 0, 0], [], [0, 0, 255]],  # Contains empty list
            [[255, 0, 0], None, [0, 0, 255]],  # Contains None (will raise TypeError)
            [[255, 0, 0], "invalid", [0, 0, 255]],  # Contains non-list (will raise TypeError)
        ]

        for invalid_list in invalid_rgb_lists:
            # Expect IndexError for short/empty lists, TypeError for None/str
            if any(isinstance(item, list) and len(item) < 3 for item in invalid_list):
                with pytest.raises(IndexError):
                    vectorized_rgb_to_hsv(invalid_list)  # type: ignore
            elif any(not isinstance(item, list) for item in invalid_list):
                with pytest.raises(TypeError):
                    vectorized_rgb_to_hsv(invalid_list)  # type: ignore

    def test_vectorized_hsv_to_rgb(self):
        """Test vectorized_hsv_to_rgb with various inputs."""
        # Test with standard colors
        hsv_colors = [
            [0, 100, 100],  # Red in HSV
            [120, 100, 100],  # Green in HSV
            [240, 100, 100],  # Blue in HSV
        ]
        expected_rgb = [[255, 0, 0], [0, 255, 0], [0, 0, 255]]  # Red  # Green  # Blue
        rgb_colors = vectorized_hsv_to_rgb(hsv_colors)
        assert rgb_colors == expected_rgb

    def test_vectorized_hsv_to_rgb_empty_input(self):
        """Test vectorized_hsv_to_rgb with empty input."""
        # Explicitly test the empty list case to ensure coverage
        assert vectorized_hsv_to_rgb([]) == []

    def test_vectorized_hsv_to_rgb_invalid_input(self):
        """Test vectorized_hsv_to_rgb with invalid HSV values that trigger exception handling."""
        # Invalid HSV colors that will trigger the exception handling
        hsv_colors = [
            [0, 100, 100],  # Valid
            [120],  # Invalid (too short) - should trigger IndexError
            [],  # Invalid (empty) - should trigger IndexError
        ]

        # The function should handle exceptions and return [0,0,0] for invalid inputs
        rgb_colors = vectorized_hsv_to_rgb(hsv_colors)
        assert len(rgb_colors) == 3
        assert rgb_colors[0] == [255, 0, 0]  # Valid color converted
        assert rgb_colors[1] == [0, 0, 0]  # Invalid color returns default
        assert rgb_colors[2] == [0, 0, 0]  # Empty list returns default

    def test_batch_color_distance(self):
        """Test batch_color_distance with various inputs."""
        # Base color for comparison
        base_color = [100, 150, 200]

        # Colors to compare against
        comparison_colors = [
            [100, 150, 200],  # Identical (distance should be 0)
            [105, 155, 205],  # Slightly different
            [200, 100, 50],  # Very different
        ]

        # Calculate distances
        distances = batch_color_distance(base_color, comparison_colors)

        # Check results
        assert len(distances) == 3
        assert distances[0] == 0.0  # Identical colors
        assert 0 < distances[1] < 20  # Slightly different (small distance)
        assert distances[2] > 100  # Very different (large distance)

        # Compare with individual calculations to verify consistency
        for i, color in enumerate(comparison_colors):
            individual_distance = calculate_color_distance(base_color, color)
            assert distances[i] == individual_distance

    def test_batch_color_distance_empty_colors(self):
        """Test batch_color_distance with empty color list."""
        # Test with valid base color but empty colors list
        base_color = [100, 150, 200]
        assert batch_color_distance(base_color, []) == []

    def test_batch_color_distance_invalid_base_color(self):
        """Test batch_color_distance with invalid base color."""
        # Test with invalid base color (too short)
        comparison_colors = [[255, 0, 0], [0, 255, 0]]

        # Base color with fewer than 3 elements should return empty list
        assert batch_color_distance([100], comparison_colors) == []
        assert batch_color_distance([100, 150], comparison_colors) == []
        assert batch_color_distance([], comparison_colors) == []

    def test_batch_color_distance_invalid_inputs(self):
        """Test batch_color_distance with both empty colors and invalid base color."""
        # Test both conditions that trigger the early return
        assert batch_color_distance([100], []) == []  # Both invalid
        assert batch_color_distance([], []) == []  # Both empty

    def test_performance_comparison(self, run_performance_tests):
        """Compare performance of vectorized operations vs. individual processing."""
        # Only run detailed performance tests when explicitly running this test
        if not run_performance_tests:
            pytest.skip("Performance tests only run with --runperf flag")

        # Create a large list of colors for testing
        colors = []
        for r in range(0, 255, 25):
            for g in range(0, 255, 25):
                for b in range(0, 255, 25):
                    colors.append([r, g, b])

        # Should have around 11^3 = 1,331 colors

        # Test vectorized RGB to HSV
        start_time = time.time()
        vectorized_result = vectorized_rgb_to_hsv(colors)
        vectorized_time = time.time() - start_time

        # Test individual RGB to HSV
        start_time = time.time()
        individual_result = []
        for color in colors:
            individual_result.append(rgb_to_hsv(color))
        individual_time = time.time() - start_time

        # Verify results are the same
        for i in range(len(colors)):
            for j in range(3):
                assert abs(vectorized_result[i][j] - individual_result[i][j]) <= 0.5

        # Vectorized should be faster (or at least not significantly slower)
        # This is a soft assertion since performance can vary
        assert (
            vectorized_time <= individual_time * 1.2
        ), f"Vectorized operation took {vectorized_time:.4f}s vs individual {individual_time:.4f}s"

        # Print performance comparison
        print(f"\nVectorized RGB→HSV: {vectorized_time:.4f}s")
        print(f"Individual RGB→HSV: {individual_time:.4f}s")
        print(f"Speedup factor: {individual_time/vectorized_time:.2f}x")

        # Similar test for HSV to RGB conversion
        hsv_colors = individual_result  # Use the HSV colors from previous test

        start_time = time.time()
        vectorized_rgb_result = vectorized_hsv_to_rgb(hsv_colors)
        vectorized_time = time.time() - start_time

        start_time = time.time()
        individual_rgb_result = []
        for hsv in hsv_colors:
            individual_rgb_result.append(hsv_to_rgb(hsv))
        individual_time = time.time() - start_time

        # Verify results are the same
        for i in range(len(colors)):
            assert vectorized_rgb_result[i] == individual_rgb_result[i]

        # Print performance comparison
        print(f"Vectorized HSV→RGB: {vectorized_time:.4f}s")
        print(f"Individual HSV→RGB: {individual_time:.4f}s")
        print(f"Speedup factor: {individual_time/vectorized_time:.2f}x")
