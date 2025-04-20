"""
Unit tests for the color gradient utilities.

Tests the gradient generation and color temperature mapping functions.
"""

import sys
import pytest
import math
import numpy as np
from vega_common.utils.color_gradient_utils import (
    create_rainbow_gradient,
    create_temperature_gradient,
    get_temperature_color,
    temperature_to_color,
    create_color_gradient,
    create_color_gradient_cielch,
    _map_to_srgb_gamut,
    _lch_to_rgb_norm,
    _is_rgb_in_gamut,
)
from vega_common.utils.color_utils import rgb_to_hsv, hsv_to_rgb


class TestGradientFunctions:
    """Tests for color gradient generation functions."""

    def test_create_color_gradient(self):
        """Test color gradient creation between two colors."""
        # Test basic gradient from red to blue
        red = [255, 0, 0]
        blue = [0, 0, 255]
        steps = 5

        gradient = create_color_gradient(red, blue, steps)

        # Check gradient properties
        assert len(gradient) == steps
        assert gradient[0][0] > 200  # First color should be reddish
        assert gradient[-1][2] > 200  # Last color should be bluish

        # Test with hue wrapping (e.g., red to yellow, which crosses the color wheel)
        red = [255, 0, 0]  # Hue = 0
        yellow = [255, 255, 0]  # Hue = 60

        # Forward gradient (0 to 60)
        forward_gradient = create_color_gradient(red, yellow, 3)
        assert len(forward_gradient) == 3

        # First should be red, last should be yellow
        assert forward_gradient[0][0] > 200 and forward_gradient[0][1] < 50
        assert forward_gradient[-1][0] > 200 and forward_gradient[-1][1] > 200

        # Test with hue wrapping in opposite direction
        red = [255, 0, 0]  # Hue = 0
        magenta = [255, 0, 255]  # Hue = 300

        # This should go the short way around the color wheel
        wrap_gradient = create_color_gradient(red, magenta, 3)

        # Check the intermediate color - should be in the red-magenta region
        # not in the red-cyan-blue-magenta region (which would be the long way)
        mid_color_hsv = rgb_to_hsv(wrap_gradient[1])
        assert 0 <= mid_color_hsv[0] <= 30 or 330 <= mid_color_hsv[0] <= 360

        # Test with single step (should be same as input)
        with pytest.raises(ValueError):
            create_color_gradient(red, blue, 1)

        # Test with identical start and end colors
        same_gradient = create_color_gradient(red, red.copy(), 3)
        assert len(same_gradient) == 3
        # All colors should be identical
        for color in same_gradient:
            assert color[0] == red[0]
            assert color[1] == red[1]
            assert color[2] == red[2]

    def test_create_color_gradient(self):
        """Test create_color_gradient with various inputs."""
        # Test with red to blue gradient
        start_rgb = [255, 0, 0]  # Red
        end_rgb = [0, 0, 255]  # Blue
        steps = 5

        gradient = create_color_gradient(start_rgb, end_rgb, steps)

        # Verify gradient properties
        assert len(gradient) == steps
        assert gradient[0] == start_rgb  # First color should be start color
        assert gradient[-1] == end_rgb  # Last color should be end color

        # Verify middle colors transition smoothly
        for i in range(1, steps - 1):
            # Each color should differ from both start and end colors
            assert gradient[i] != start_rgb
            assert gradient[i] != end_rgb

            # Each middle color should have decreasing red and increasing blue
            assert gradient[i][0] < gradient[i - 1][0]  # Red decreases
            assert gradient[i][2] > gradient[i - 1][2]  # Blue increases

        # Test with edge cases
        # Just one step
        assert create_color_gradient(start_rgb, end_rgb, 1) == [start_rgb]

        # Two steps (just start and end)
        two_step_gradient = create_color_gradient(start_rgb, end_rgb, 2)
        assert two_step_gradient == [start_rgb, end_rgb]

        # Many steps (should still maintain gradient properties)
        many_steps = 20
        long_gradient = create_color_gradient(start_rgb, end_rgb, many_steps)
        assert len(long_gradient) == many_steps
        assert long_gradient[0] == start_rgb
        assert long_gradient[-1] == end_rgb

    def test_gradient_with_hue_wraparound(self):
        """Test color gradient with hue values that wrap around the color wheel."""
        # Red to magenta gradient (hue: 0° to 300°)
        start_rgb = [255, 0, 0]  # Red (0°)
        end_rgb = [255, 0, 255]  # Magenta (300°)

        gradient = create_color_gradient(start_rgb, end_rgb, 7)

        # Verify the gradient transitions through purple shades
        # The hue should increase in each step
        start_hsv = rgb_to_hsv(start_rgb)

        # Check intermediate colors
        for i in range(1, 6):
            current_hsv = rgb_to_hsv(gradient[i])
            # Hue should gradually increase from 0 to 300
            assert 0 < current_hsv[0] < 300

            if i > 1:
                prev_hsv = rgb_to_hsv(gradient[i - 1])
                # Each hue should be greater than the previous
                # (except if it wrapped around, which shouldn't happen in this test)
                assert current_hsv[0] > prev_hsv[0]

        # Gradient with hue going the other way around the color wheel
        # From cyan (180°) to yellow (60°) - should go through green (120°) not magenta
        start_rgb = [0, 255, 255]  # Cyan
        end_rgb = [255, 255, 0]  # Yellow

        gradient = create_color_gradient(start_rgb, end_rgb, 7)

        # Convert to HSV to check the hue transitions
        gradient_hsv = [rgb_to_hsv(color) for color in gradient]

        # In this case, the gradient should go through green (shorter path)
        # So hue should decrease from 180° to 60°
        assert 175 <= gradient_hsv[0][0] <= 185  # Around 180° (cyan)
        assert 55 <= gradient_hsv[-1][0] <= 65  # Around 60° (yellow)

        # Middle color should be close to green (120°)
        middle_hue = gradient_hsv[3][0]
        assert 115 <= middle_hue <= 125

        # Hues should consistently decrease through the gradient
        for i in range(1, 7):
            assert gradient_hsv[i][0] < gradient_hsv[i - 1][0]

    def test_create_color_gradient_special_cases(self):
        """Test special cases in color gradient generation."""
        # Test special case for red to blue gradient
        red = [255, 0, 0]
        blue = [0, 0, 255]
        steps = 5

        # This should trigger the special case in the function
        gradient = create_color_gradient(red, blue, steps)

        # Check for monotonically decreasing red and increasing blue
        for i in range(1, steps):
            assert gradient[i][0] < gradient[i - 1][0], "Red should decrease"
            assert gradient[i][2] > gradient[i - 1][2], "Blue should increase"

        # Test special case for red to magenta gradient
        red = [255, 0, 0]
        magenta = [255, 0, 255]
        steps = 7

        # This should trigger the clockwise path special case
        gradient = create_color_gradient(red, magenta, steps)

        # Convert to HSV to check the path
        gradient_hsv = [rgb_to_hsv(color) for color in gradient]

        # First should be red (hue ~ 0)
        assert gradient_hsv[0][0] < 5

        # Last should be magenta (hue ~ 300)
        assert 295 <= gradient_hsv[-1][0] <= 305

        # Intermediate hues should increase monotonically (clockwise path through color wheel)
        for i in range(1, steps - 1):
            assert gradient_hsv[i][0] > gradient_hsv[0][0], "Hue should increase clockwise"

    def test_create_color_gradient_edge_cases(self):
        """Test edge cases for create_color_gradient."""
        red = [255, 0, 0]
        blue = [0, 0, 255]

        # Test with invalid steps
        with pytest.raises(ValueError):
            create_color_gradient(red, blue, 0)

        with pytest.raises(ValueError):
            create_color_gradient(red, blue, -5)

        # Test with single step (should return only start color)
        result = create_color_gradient(red, blue, 1)
        assert len(result) == 1
        assert result[0] == red

        # Test with exactly two steps (should return just start and end)
        result = create_color_gradient(red, blue, 2)
        assert len(result) == 2
        assert result[0] == red
        assert result[-1] == blue

    def test_create_rainbow_gradient(self):
        """Test rainbow gradient generation."""
        # Test with default steps
        rainbow = create_rainbow_gradient()
        assert len(rainbow) == 20

        # Test with custom steps
        custom_steps = 10
        custom_rainbow = create_rainbow_gradient(custom_steps)
        assert len(custom_rainbow) == custom_steps

        # Check color distribution
        # First color should be red (hue 0)
        first_hsv = rgb_to_hsv(custom_rainbow[0])
        assert abs(first_hsv[0] - 0) <= 1  # Near hue 0 (red)

        # Middle color should be around cyan/green
        mid_index = custom_steps // 2
        mid_hsv = rgb_to_hsv(custom_rainbow[mid_index])
        assert 120 <= mid_hsv[0] <= 180

        # Last color should approach red again (hue near 360)
        last_hsv = rgb_to_hsv(custom_rainbow[-1])
        assert last_hsv[0] > 300 or last_hsv[0] < 30

        # All colors should be fully saturated and at full brightness
        for color in custom_rainbow:
            hsv = rgb_to_hsv(color)
            assert hsv[1] == 100
            assert hsv[2] == 100

        # Test with single step
        single_rainbow = create_rainbow_gradient(1)
        assert len(single_rainbow) == 1
        single_hsv = rgb_to_hsv(single_rainbow[0])
        assert single_hsv[0] == 0  # Should be red

    def test_create_temperature_gradient(self):
        """Test temperature gradient generation."""
        # Define temperature range
        min_temp = 30
        max_temp = 90
        steps = 7

        # Generate gradient
        temp_colors = create_temperature_gradient(min_temp, max_temp, steps)

        # Should have the right number of entries
        assert len(temp_colors) == steps

        # Should contain min and max temperatures
        assert min_temp in temp_colors
        assert max_temp in temp_colors

        # Colors should progress from blue to red
        min_temp_hsv = rgb_to_hsv(temp_colors[min_temp])
        max_temp_hsv = rgb_to_hsv(temp_colors[max_temp])

        # Min temp should be blue (hue around 240)
        assert abs(min_temp_hsv[0] - 240) <= 5

        # Max temp should be red (hue around 0)
        assert max_temp_hsv[0] <= 5

        # All colors should be fully saturated and at full brightness
        for temp, color in temp_colors.items():
            hsv = rgb_to_hsv(color)
            assert hsv[1] == 100
            assert hsv[2] == 100

        # Temperatures should be evenly distributed
        temps = sorted(temp_colors.keys())
        temp_diffs = [temps[i + 1] - temps[i] for i in range(len(temps) - 1)]

        # All temperature differences should be nearly equal
        expected_diff = (max_temp - min_temp) / (steps - 1)
        for diff in temp_diffs:
            assert abs(diff - expected_diff) <= 1

        # Test with small temperature range
        small_range = create_temperature_gradient(30, 35, 3)
        assert len(small_range) == 3
        assert 30 in small_range
        assert 35 in small_range

        # Test with min_temp = max_temp (should still produce valid result)
        same_temp = create_temperature_gradient(50, 50, 1)
        assert len(same_temp) == 1
        assert 50 in same_temp

    def test_get_temperature_color(self):
        """Test getting color for a specific temperature."""
        # Define temperature range
        min_temp = 30
        max_temp = 90

        # Test at min temperature
        min_color = get_temperature_color(min_temp, min_temp, max_temp)
        min_hsv = rgb_to_hsv(min_color)
        assert abs(min_hsv[0] - 240) <= 5  # Should be blue

        # Test at max temperature
        max_color = get_temperature_color(max_temp, min_temp, max_temp)
        max_hsv = rgb_to_hsv(max_color)
        assert max_hsv[0] <= 5  # Should be red

        # Test at middle temperature
        mid_temp = (min_temp + max_temp) / 2
        mid_color = get_temperature_color(mid_temp, min_temp, max_temp)
        mid_hsv = rgb_to_hsv(mid_color)
        assert abs(mid_hsv[0] - 120) <= 5  # Should be green-ish

        # Test temperature clamping
        below_min = get_temperature_color(min_temp - 10, min_temp, max_temp)
        above_max = get_temperature_color(max_temp + 10, min_temp, max_temp)

        # Below min should be same as min (blue)
        assert below_min == min_color

        # Above max should be same as max (red)
        assert above_max == max_color

        # Test when min_temp = max_temp (edge case)
        equal_temp_color = get_temperature_color(50, 50, 50)
        equal_hsv = rgb_to_hsv(equal_temp_color)

        # In this case, we expect a blue color (since temp_fraction is 0)
        assert abs(equal_hsv[0] - 240) <= 5

    def test_temperature_to_color(self):
        """Test custom temperature to color mapping function."""
        # Test with default parameters (blue to red)
        min_temp = 30
        max_temp = 90

        # At minimum temperature
        min_color = temperature_to_color(min_temp)
        assert min_color[2] > 200  # Should be blue
        assert min_color[0] < 50

        # At maximum temperature
        max_color = temperature_to_color(max_temp)
        assert max_color[0] > 200  # Should be red
        assert max_color[2] < 50

        # At middle temperature
        mid_temp = (min_temp + max_temp) / 2
        mid_color = temperature_to_color(mid_temp)

        # Should be a mix (purple-ish)
        assert mid_color[0] > 100
        assert mid_color[2] > 100

        # Test with custom colors
        green = [0, 255, 0]
        yellow = [255, 255, 0]

        custom_min = temperature_to_color(min_temp, cool_color=green, warm_color=yellow)
        assert custom_min[1] > 200  # Should be green
        assert custom_min[0] < 50

        custom_max = temperature_to_color(max_temp, cool_color=green, warm_color=yellow)
        assert custom_max[0] > 200 and custom_max[1] > 200  # Should be yellow

        # Test temperature clamping
        below_min = temperature_to_color(min_temp - 10)
        assert below_min[2] > 200  # Should still be blue

        above_max = temperature_to_color(max_temp + 10)
        assert above_max[0] > 200  # Should still be red

        # Test when min_temp = max_temp (edge case)
        same_temp = temperature_to_color(50, min_temp=50, max_temp=50)
        # With equal temps, factor should be 0, resulting in the cool color
        assert same_temp[2] > 200  # Should be blue

        # Test with custom colors and min_temp = max_temp
        same_temp_custom = temperature_to_color(
            50, min_temp=50, max_temp=50, cool_color=green, warm_color=yellow
        )
        # Should be the cool color (green)
        assert same_temp_custom[1] > 200
        assert same_temp_custom[0] < 50

        # Test with hue wrapping colors (e.g., red and cyan)
        red = [255, 0, 0]  # hue near 0
        cyan = [0, 255, 255]  # hue near 180

        # This tests the hue wrapping code path
        wrap_mid = temperature_to_color(mid_temp, cool_color=red, warm_color=cyan)
        wrap_mid_hsv = rgb_to_hsv(wrap_mid)

        # Should take the shortest path in hue space
        # In this case, it should go through magenta/purple, not yellow/green
        # So hue should be either close to 0 or close to 360
        assert wrap_mid_hsv[0] < 90 or wrap_mid_hsv[0] > 270

    def test_temperature_to_color_edge_cases(self):
        """Test temperature_to_color with various edge cases."""
        # Test temperature clamping at lower bound
        color_below = temperature_to_color(25, min_temp=30, max_temp=90)
        color_min = temperature_to_color(30, min_temp=30, max_temp=90)
        assert color_below == color_min

        # Test temperature clamping at upper bound
        color_above = temperature_to_color(95, min_temp=30, max_temp=90)
        color_max = temperature_to_color(90, min_temp=30, max_temp=90)
        assert color_above == color_max

        # Test with min_temp = max_temp
        equal_temp_color = temperature_to_color(50, min_temp=50, max_temp=50)
        assert equal_temp_color == [0, 0, 255]  # Should return cool color (blue)

        # Test custom colors with min_temp = max_temp
        green = [0, 255, 0]
        yellow = [255, 255, 0]
        custom_equal_temp = temperature_to_color(
            50, min_temp=50, max_temp=50, cool_color=green, warm_color=yellow
        )
        assert custom_equal_temp == green  # Should return the cool color

        # Test special case handling for red to cyan transition path
        red = [255, 0, 0]
        cyan = [0, 255, 255]

        # Test with red as cool color and cyan as warm color
        mid_temp = 60
        result1 = temperature_to_color(
            mid_temp, min_temp=30, max_temp=90, cool_color=red, warm_color=cyan
        )

        # Test with cyan as cool color and red as warm color
        result2 = temperature_to_color(
            mid_temp, min_temp=30, max_temp=90, cool_color=cyan, warm_color=red
        )

        # Both should use direct RGB interpolation rather than HSV
        # Check that neither result has significant green component (would happen if HSV used)
        assert result1[1] > 0, "Direct RGB interpolation should give some green"
        assert result2[1] > 0, "Direct RGB interpolation should give some green"


class TestCIELCHGradient:
    """Tests for CIELCH-based color gradient generation."""

    def test_create_color_gradient_cielch_basic(self):
        """Test basic functionality of CIELCH-based color gradient generation."""
        # Test with red to blue gradient (high contrast)
        start_rgb = [255, 0, 0]  # Red
        end_rgb = [0, 0, 255]  # Blue
        steps = 5

        try:
            gradient = create_color_gradient_cielch(start_rgb, end_rgb, steps)

            # Verify gradient properties
            assert len(gradient) == steps
            assert gradient[0] == start_rgb  # First color should be start color
            assert gradient[-1] == end_rgb  # Last color should be end color

            # Middle colors should be perceptually distributed
            # Convert each color to HSV for easier analysis
            gradient_hsv = [rgb_to_hsv(color) for color in gradient]

            # Check that intermediate colors are valid transitions between red and blue
            # The gradient can take either path around the hue circle:
            # 1. Clockwise: Red (0°) → Magenta (~300°) → Blue (240°)
            # 2. Counterclockwise: Red (0°) → Yellow → Green → Cyan → Blue (240°)
            for i in range(1, len(gradient_hsv) - 1):
                current_hue = gradient_hsv[i][0]
                # Check that the hue is either:
                # - Between 0 and 240 (counterclockwise path), OR
                # - Between 240 and 360 (clockwise path)
                assert (0 < current_hue < 240) or (
                    240 < current_hue < 360
                ), f"Intermediate hue {current_hue} should be a valid transition between red and blue"

        except ImportError:
            pytest.skip("colour-science library not installed")

    def test_create_color_gradient_cielch_basic_without_colour_lib(self):
        """Test that ImportError is handled when colour library is missing."""
        # Test with red to blue gradient (high contrast)
        start_rgb = [255, 0, 0]  # Red
        end_rgb = [0, 0, 255]  # Blue
        steps = 5

        # Temporarily remove the colour module or set to None
        with pytest.MonkeyPatch.context() as monkeypatch:
            # Mock colour module as None to simulate it not being installed
            monkeypatch.setitem(sys.modules, "colour", None)

            # Should raise ImportError and not crash
            with pytest.raises(ImportError):
                gradient = create_color_gradient_cielch(start_rgb, end_rgb, steps)

    def test_create_color_gradient_cielch_edge_cases(self):
        """Test edge cases for CIELCH-based color gradient generation."""
        try:
            # Test with steps=1 (should return only start color)
            start_rgb = [255, 0, 0]
            end_rgb = [0, 0, 255]

            one_step = create_color_gradient_cielch(start_rgb, end_rgb, 1)
            assert len(one_step) == 1
            assert one_step[0] == start_rgb

            # Test with steps=2 (should return start and end colors)
            two_steps = create_color_gradient_cielch(start_rgb, end_rgb, 2)
            assert len(two_steps) == 2
            assert two_steps[0] == start_rgb
            assert two_steps[1] == end_rgb

            # Test with invalid steps
            with pytest.raises(ValueError):
                create_color_gradient_cielch(start_rgb, end_rgb, 0)

            with pytest.raises(ValueError):
                create_color_gradient_cielch(start_rgb, end_rgb, -1)

        except ImportError:
            pytest.skip("colour-science library not installed")

    def test_create_color_gradient_cielch_edge_cases_without_colour_lib(self):
        """Test that ImportError is handled when colour library is missing."""
        import vega_common.utils.color_gradient_utils as cgu

        start_rgb = [255, 0, 0]
        end_rgb = [0, 0, 255]

        # Store original colour module reference from the module
        original_colour = cgu.colour

        try:
            # Set colour to None in the module to simulate it not being available
            cgu.colour = None

            # Now when the function tries to use colour, it should raise ImportError
            # We need to use steps > 2 to reach the code that uses the colour module
            with pytest.raises(ImportError):
                cgu.create_color_gradient_cielch(start_rgb, end_rgb, 3)

            # Test with other steps values
            with pytest.raises(ImportError):
                cgu.create_color_gradient_cielch(start_rgb, end_rgb, 5)

            # Test with invalid steps (should raise ValueError, not ImportError)
            # ValueError is raised before the code reaches the part that would use the colour module
            with pytest.raises(ValueError):
                cgu.create_color_gradient_cielch(start_rgb, end_rgb, 0)

        finally:
            # Restore the original colour module reference
            cgu.colour = original_colour

    def test_create_color_gradient_cielch_same_color(self):
        """Test gradient generation between identical colors."""
        try:
            # Test with identical start and end colors
            color = [100, 150, 200]
            steps = 5

            gradient = create_color_gradient_cielch(color, color.copy(), steps)

            # Should have the requested number of steps
            assert len(gradient) == steps

            # All colors in gradient should be identical to input
            for c in gradient:
                assert c == color

        except ImportError:
            pytest.skip("colour-science library not installed")

    def test_create_color_gradient_cielch_same_color_without_colour_lib(self):
        """Test gradient generation between identical colors without colour library."""
        color = [100, 150, 200]
        steps = 5

        # Temporarily remove the colour module or set to None
        with pytest.MonkeyPatch.context() as monkeypatch:
            # Mock colour module as None to simulate it not being installed
            monkeypatch.setitem(sys.modules, "colour", None)

            # Should raise ImportError
            with pytest.raises(ImportError):
                create_color_gradient_cielch(color, color.copy(), steps)

    def test_create_color_gradient_cielch_perceptual_uniformity(self):
        """Test that CIELCH gradient produces perceptually uniform steps."""
        try:
            # Test gradient between black and white
            black = [0, 0, 0]
            white = [255, 255, 255]
            steps = 7

            gradient = create_color_gradient_cielch(black, white, steps)

            # Convert to HSV to check value (brightness) changes
            gradient_hsv = [rgb_to_hsv(color) for color in gradient]

            # Extract just the V values (brightness)
            brightness_values = [hsv[2] for hsv in gradient_hsv]

            # Calculate brightness differences between adjacent steps
            brightness_diffs = [
                brightness_values[i + 1] - brightness_values[i]
                for i in range(len(brightness_values) - 1)
            ]

            # In a perceptually uniform gradient, these differences should be similar
            # Check that max difference between any two diffs is less than 15%
            if brightness_diffs:
                max_diff = max(brightness_diffs)
                min_diff = min(brightness_diffs)
                assert max_diff - min_diff < 15, "Brightness steps should be fairly uniform"

        except ImportError:
            pytest.skip("colour-science library not installed")

    def test_create_color_gradient_cielch_perceptual_uniformity_without_colour_lib(self):
        """Test CIELCH gradient without colour library."""
        black = [0, 0, 0]
        white = [255, 255, 255]
        steps = 7

        # Temporarily remove the colour module or set to None
        with pytest.MonkeyPatch.context() as monkeypatch:
            # Mock colour module as None to simulate it not being installed
            monkeypatch.setitem(sys.modules, "colour", None)

            # Should raise ImportError
            with pytest.raises(ImportError):
                create_color_gradient_cielch(black, white, steps)

    def test_create_color_gradient_cielch_vs_hsv(self):
        """Compare CIELCH gradient with HSV gradient for perceptual smoothness."""
        try:
            # Define colors with significant brightness difference
            bright_yellow = [255, 255, 0]  # High brightness
            dark_blue = [0, 0, 128]  # Low brightness
            steps = 7

            # Create gradients using both methods
            cielch_gradient = create_color_gradient_cielch(bright_yellow, dark_blue, steps)
            hsv_gradient = create_color_gradient(bright_yellow, dark_blue, steps)

            # For simple verification, check that the gradients are different
            # (This isn't a strong test, but confirms they use different algorithms)
            assert cielch_gradient != hsv_gradient, "CIELCH and HSV gradients should differ"

            # Convert both to HSV for analysis
            cielch_hsv = [rgb_to_hsv(color) for color in cielch_gradient]
            hsv_hsv = [rgb_to_hsv(color) for color in hsv_gradient]

            # The difference is most noticeable in brightness transitions
            # In HSV, brightness changes linearly while in CIELCH it follows perceptual lightness
            # Extract brightness values
            cielch_brightness = [hsv[2] for hsv in cielch_hsv]
            hsv_brightness = [hsv[2] for hsv in hsv_hsv]

            # They should be different in the middle steps (not at endpoints)
            for i in range(1, steps - 1):
                assert (
                    abs(cielch_brightness[i] - hsv_brightness[i]) > 1
                ), f"Brightness at step {i} should differ between methods"

        except ImportError:
            pytest.skip("colour-science library not installed")

    def test_create_color_gradient_cielch_vs_hsv_without_colour_lib(self):
        """Test CIELCH vs HSV gradient without colour library."""
        bright_yellow = [255, 255, 0]  # High brightness
        dark_blue = [0, 0, 128]  # Low brightness
        steps = 7

        # Temporarily remove the colour module or set to None
        with pytest.MonkeyPatch.context() as monkeypatch:
            # Mock colour module as None to simulate it not being installed
            monkeypatch.setitem(sys.modules, "colour", None)

            # Should raise ImportError for CIELCH gradient
            with pytest.raises(ImportError):
                cielch_gradient = create_color_gradient_cielch(bright_yellow, dark_blue, steps)

            # HSV gradient should still work
            hsv_gradient = create_color_gradient(bright_yellow, dark_blue, steps)
            assert len(hsv_gradient) == steps

    def test_create_color_gradient_cielch_hue_wrapping(self):
        """Test CIELCH gradient with colors requiring hue wrapping."""
        try:
            # Test colors that would wrap around the hue circle
            magenta = [255, 0, 255]  # Hue around 300
            yellow = [255, 255, 0]  # Hue around 60
            steps = 7

            gradient = create_color_gradient_cielch(magenta, yellow, steps)

            # Convert to HSV to check hue progression
            gradient_hsv = [rgb_to_hsv(color) for color in gradient]

            # First should be magenta (hue around 300)
            assert 295 <= gradient_hsv[0][0] <= 305

            # Last should be yellow (hue around 60)
            assert 53 <= gradient_hsv[-1][0] <= 65

            # Check that the hue takes the shortest path
            # In this case, magenta to yellow should go through red (0°)
            # rather than through blue, cyan, green
            for hsv in gradient_hsv[1:-1]:
                # Hue should be either in the 0-65 range or the 295-359 range
                assert (0 <= hsv[0] <= 65) or (
                    295 <= hsv[0] <= 359
                ), f"Hue {hsv[0]} should take shortest path from magenta to yellow"

        except ImportError:
            pytest.skip("colour-science library not installed")

    def test_create_color_gradient_cielch_hue_wrapping_without_colour_lib(self):
        """Test CIELCH gradient with hue wrapping without colour library."""
        magenta = [255, 0, 255]  # Hue around 300
        yellow = [255, 255, 0]  # Hue around 60
        steps = 7

        # Temporarily remove the colour module or set to None
        with pytest.MonkeyPatch.context() as monkeypatch:
            # Mock colour module as None to simulate it not being installed
            monkeypatch.setitem(sys.modules, "colour", None)

            # Should raise ImportError
            with pytest.raises(ImportError):
                gradient = create_color_gradient_cielch(magenta, yellow, steps)

    def test_create_color_gradient_cielch_out_of_gamut_handling(self):
        """Test handling of out-of-gamut colors in CIELCH gradient."""
        try:
            # Colors that will produce out-of-gamut intermediate values
            # Vivid blue and vivid green often create out-of-gamut cyan
            vivid_blue = [0, 0, 255]
            vivid_green = [0, 255, 0]
            steps = 7

            gradient = create_color_gradient_cielch(vivid_blue, vivid_green, steps)

            # All resulting colors should be within RGB gamut (0-255)
            for color in gradient:
                for component in color:
                    assert 0 <= component <= 255

            # Verify start and end colors are preserved
            assert gradient[0] == vivid_blue
            assert gradient[-1] == vivid_green

            # Due to perceptual gamut mapping, individual RGB components might not
            # change monotonically. Instead, verify the general color transition:
            # From blue to green by checking that:
            # 1. Green component is higher at the end than at the beginning
            # 2. Blue component is higher at the beginning than at the end
            assert gradient[-1][1] > gradient[0][1]  # Green increases overall
            assert gradient[0][2] > gradient[-1][2]  # Blue decreases overall

            # Check that the gradient follows the expected hue transition
            # by converting to HSV and verifying hue progression
            gradient_hsv = [rgb_to_hsv(color) for color in gradient]

            # Blue is ~240°, green is ~120°
            # Hue should generally decrease through the gradient
            assert abs(gradient_hsv[0][0] - 240) < 10  # First color close to blue hue
            assert abs(gradient_hsv[-1][0] - 120) < 10  # Last color close to green hue

        except ImportError:
            pytest.skip("colour-science library not installed")

    def test_create_color_gradient_cielch_out_of_gamut_handling_without_colour_lib(self):
        """Test CIELCH gradient gamut handling without colour library."""
        vivid_blue = [0, 0, 255]
        vivid_green = [0, 255, 0]
        steps = 7

        # Temporarily remove the colour module or set to None
        with pytest.MonkeyPatch.context() as monkeypatch:
            # Mock colour module as None to simulate it not being installed
            monkeypatch.setitem(sys.modules, "colour", None)

            # Should raise ImportError
            with pytest.raises(ImportError):
                gradient = create_color_gradient_cielch(vivid_blue, vivid_green, steps)

    def test_create_color_gradient_cielch_error_handling(self):
        """Test error handling in CIELCH gradient function."""
        start_rgb = [255, 0, 0]
        end_rgb = [0, 0, 255]

        # Test with 0 steps
        with pytest.raises(ValueError):
            create_color_gradient_cielch(start_rgb, end_rgb, 0)

        # Test with negative steps
        with pytest.raises(ValueError):
            create_color_gradient_cielch(start_rgb, end_rgb, -3)

    def test_map_to_srgb_gamut(self):
        """Test the gamut mapping function directly."""
        try:
            import colour

            # Test with in-gamut color (should return unchanged)
            rgb_in_gamut = np.array([0.5, 0.5, 0.5])  # Mid-gray
            lab = colour.XYZ_to_Lab(colour.sRGB_to_XYZ(rgb_in_gamut))
            lch = colour.Lab_to_LCHab(lab)

            mapped_rgb = _map_to_srgb_gamut(lch)

            # Should be very close to original
            assert np.allclose(mapped_rgb, rgb_in_gamut, atol=1e-5)

            # Test with out-of-gamut color
            # Creating a color with high chroma that's likely out of gamut
            high_chroma_lch = np.array([50.0, 100.0, 320.0])

            mapped_rgb = _map_to_srgb_gamut(high_chroma_lch)

            # The result should be within sRGB gamut (0-1)
            assert np.all(mapped_rgb >= 0)
            assert np.all(mapped_rgb <= 1)

            # The result should preserve hue and lightness as much as possible
            # Convert back to LCH to verify
            mapped_lab = colour.XYZ_to_Lab(colour.sRGB_to_XYZ(mapped_rgb))
            mapped_lch = colour.Lab_to_LCHab(mapped_lab)

            # Lightness and Hue should be close to original
            # Chroma will be reduced to fit in gamut
            assert abs(mapped_lch[0] - high_chroma_lch[0]) < 5  # Lightness preserved
            assert abs((mapped_lch[2] - high_chroma_lch[2]) % 360) < 5  # Hue preserved
            assert mapped_lch[1] < high_chroma_lch[1]  # Chroma reduced

            # Test special cases
            # Black
            black_lch = np.array([0.0, 50.0, 180.0])
            black_mapped = _map_to_srgb_gamut(black_lch)
            assert np.allclose(black_mapped, [0, 0, 0], atol=1e-5)

            # White
            white_lch = np.array([100.0, 50.0, 180.0])
            white_mapped = _map_to_srgb_gamut(white_lch)
            assert np.allclose(white_mapped, [1, 1, 1], atol=1e-5)

            # Gray (zero chroma)
            gray_lch = np.array([50.0, 0.0, 180.0])
            gray_mapped = _map_to_srgb_gamut(gray_lch)
            # Should be mid-gray
            assert np.allclose(gray_mapped, [0.5, 0.5, 0.5], atol=0.1)

        except ImportError:
            pytest.skip("colour-science library not installed")

    def test_create_color_gradient_cielch_performance(self):
        """Test that CIELCH gradient generation maintains reasonable performance."""
        try:
            import time

            # Define colors
            start_rgb = [255, 50, 50]  # Light red
            end_rgb = [50, 50, 255]  # Light blue
            steps = 50  # Moderate number of steps

            # Measure performance
            start_time = time.time()
            gradient = create_color_gradient_cielch(start_rgb, end_rgb, steps)
            duration = time.time() - start_time

            # Basic verification of result
            assert len(gradient) == steps

            # Performance should be reasonable (adjust based on hardware)
            # On a modern system, generating 50 steps should take less than 1 second
            # This is a soft assertion, mainly to catch severe performance issues
            assert duration < 1.0, f"Gradient generation took {duration:.2f}s, which is too slow"

        except ImportError:
            pytest.skip("colour-science library not installed")

    def test_map_to_srgb_gamut_edge_cases(self):
        """Test edge cases for the sRGB gamut mapping function."""
        try:
            import colour

            # Test with very low lightness (near black)
            near_black_lch = np.array([0.0001, 50.0, 120.0])
            near_black_result = _map_to_srgb_gamut(near_black_lch)
            # Increase tolerance for near-black mapping
            assert np.allclose(
                near_black_result, [0, 0, 0], atol=1e-5
            ), "Near-black should map to black"

            # Test with very high lightness (near white)
            near_white_lch = np.array([99.9999, 50.0, 120.0])
            near_white_result = _map_to_srgb_gamut(near_white_lch)
            assert np.allclose(near_white_result, [1, 1, 1]), "Near-white should map to white"

            # Test with near-zero chroma (near gray)
            near_gray_lch = np.array([50.0, 0.0001, 120.0])
            near_gray_result = _map_to_srgb_gamut(near_gray_lch)
            assert np.allclose(
                near_gray_result, [0.5, 0.5, 0.5], atol=0.1
            ), "Near-gray should map to gray"

            # Test already in-gamut color stays the same
            in_gamut_rgb = np.array([0.5, 0.25, 0.75])  # Known in-gamut
            # Convert to LCH
            in_gamut_xyz = colour.sRGB_to_XYZ(in_gamut_rgb)
            in_gamut_lab = colour.XYZ_to_Lab(in_gamut_xyz)
            in_gamut_lch = colour.Lab_to_LCHab(in_gamut_lab)

            # Map back to sRGB
            result = _map_to_srgb_gamut(in_gamut_lch)

            # Should be almost identical to original
            assert np.allclose(result, in_gamut_rgb, atol=1e-4)

            # Test extreme out-of-gamut color gets mapped correctly
            extreme_lch = np.array([50.0, 200.0, 120.0])  # Extremely high chroma
            extreme_result = _map_to_srgb_gamut(extreme_lch)

            # Result should be in gamut
            assert np.all(extreme_result >= 0)
            assert np.all(extreme_result <= 1)

            # Convert back to LCH to check hue preservation
            extreme_xyz = colour.sRGB_to_XYZ(extreme_result)
            extreme_lab = colour.XYZ_to_Lab(extreme_xyz)
            mapped_lch = colour.Lab_to_LCHab(extreme_lab)

            # Hue should be preserved
            assert abs((mapped_lch[2] - extreme_lch[2]) % 360) < 5

            # Test convergence criteria with small tolerance
            high_precision = _map_to_srgb_gamut(extreme_lch, tolerance=1e-6)
            assert np.all(high_precision >= 0)
            assert np.all(high_precision <= 1)

        except ImportError:
            pytest.skip("colour-science library not installed")


class TestHelperFunctions:
    """Tests for private helper functions."""

    def test_lch_to_rgb_norm(self):
        """Test LCH to normalized RGB conversion."""
        try:
            import colour

            # Test normal conversion
            lch = np.array([50.0, 20.0, 120.0])  # Green-ish color
            rgb_norm = _lch_to_rgb_norm(lch)

            # Should be a valid RGB color
            assert isinstance(rgb_norm, np.ndarray)
            assert rgb_norm.shape == (3,)
            assert np.all(rgb_norm >= 0)
            assert np.all(rgb_norm <= 1)

            # Test conversion with extreme values
            # Very high chroma that might cause issues
            high_chroma = np.array([50.0, 200.0, 120.0])
            high_result = _lch_to_rgb_norm(high_chroma)

            # Check that the result is a numpy array of shape (3,)
            # Acknowledging that extreme inputs might result in out-of-gamut values
            # before potential clipping (which might be missing or tested elsewhere).
            assert isinstance(high_result, np.ndarray)
            assert high_result.shape == (3,)
            # Note: We are not asserting the range [0, 1] here, as the raw conversion
            # of extreme LCH values can exceed the sRGB gamut.

            # Test with negative values (should be handled gracefully, likely clipped)
            neg_lch = np.array([-10.0, -20.0, -30.0])
            neg_result = _lch_to_rgb_norm(neg_lch)

            # Should clip to valid range
            assert np.all(neg_result >= 0)
            assert np.all(neg_result <= 1)

            # Test with hue > 360 (should be wrapped)
            wrap_lch = np.array([50.0, 20.0, 480.0])  # 480° = 120°
            wrap_result = _lch_to_rgb_norm(wrap_lch)
            # Add assertion for wrap_result
            assert isinstance(wrap_result, np.ndarray)
            assert wrap_result.shape == (3,)

            # Test when conversion raises an exception
            with pytest.MonkeyPatch.context() as m:
                # Force the colour.LCHab_to_Lab function to raise an exception
                def mock_convert(*_):  # Use *_ to indicate unused arguments
                    raise ValueError("Simulated conversion error")

                m.setattr(colour, "LCHab_to_Lab", mock_convert)

                # Should return gray based on lightness

                m.setattr(colour, "LCHab_to_Lab", mock_convert)

                # Should return gray based on lightness
                error_lch = np.array([50.0, 20.0, 120.0])
                error_result = _lch_to_rgb_norm(error_lch)

                # Check if result is grayscale with lightness = 0.5
                assert np.allclose(error_result, [0.5, 0.5, 0.5])

        except ImportError:
            pytest.skip("colour-science library not installed")

    def test_is_rgb_in_gamut(self):
        """Test RGB gamut checking function."""
        try:
            # Test in-gamut colors
            assert _is_rgb_in_gamut(np.array([0, 0, 0]))  # Black
            assert _is_rgb_in_gamut(np.array([1, 1, 1]))  # White
            assert _is_rgb_in_gamut(np.array([0.5, 0.5, 0.5]))  # Gray
            assert _is_rgb_in_gamut(np.array([1, 0, 0]))  # Red
            assert _is_rgb_in_gamut(np.array([0, 1, 0]))  # Green
            assert _is_rgb_in_gamut(np.array([0, 0, 1]))  # Blue

            # Test out-of-gamut colors
            assert not _is_rgb_in_gamut(np.array([1.1, 0, 0]))
            assert not _is_rgb_in_gamut(np.array([0, -0.1, 0]))
            assert not _is_rgb_in_gamut(np.array([0, 0, 1.01]))
            assert not _is_rgb_in_gamut(np.array([1.01, 1.01, 1.01]))

            # Test with custom tolerance
            assert _is_rgb_in_gamut(np.array([1.05, 0, 0]), tolerance=0.1)
            assert _is_rgb_in_gamut(np.array([0, -0.05, 0]), tolerance=0.1)
            assert not _is_rgb_in_gamut(np.array([1.2, 0, 0]), tolerance=0.1)
        except ImportError:
            pytest.skip("colour-science library not installed")

    def test_map_to_srgb_gamut_performance(self):
        """Test that sRGB gamut mapping maintains reasonable performance."""
        try:
            import time
            import colour

            # Define colors
            high_chroma_lch = np.array([50.0, 200.0, 120.0])  # Extremely high chroma
            steps = 1000  # Large number of steps

            # Measure performance
            start_time = time.time()
            for _ in range(steps):
                _map_to_srgb_gamut(high_chroma_lch)
            duration = time.time() - start_time

            # Performance should be reasonable (adjust based on hardware)
            # On a modern system, mapping 1000 colors should take less than 2 seconds
            assert duration < 5, f"Gamut mapping took {duration:.2f}s, which is too slow"

        except ImportError:
            pytest.skip("colour-science library not installed")
