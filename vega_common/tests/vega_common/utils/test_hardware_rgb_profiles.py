"""
Unit tests for the hardware_rgb_profiles module.

Tests all the hardware-specific color transformation functions to ensure
they behave as expected across different contexts.
"""
import pytest
import math
from vega_common.utils.hardware_rgb_profiles import (
    aorus_x470_hue_fix,
    asus_aura_brightness_correction,
    corsair_icue_color_mapping,
    msi_mystic_light_correction,
    asrock_polychrome_correction,
    nzxt_cam_correction,
    create_rainbow_gradient,
    create_temperature_gradient,
    get_temperature_color,
    temperature_to_color,
    create_color_gradient,
    apply_hardware_specific_correction
)
from vega_common.utils.color_utils import rgb_to_hsv, hsv_to_rgb


class TestHardwareColorCorrections:
    """Tests for hardware-specific color correction functions."""
    
    def test_aorus_x470_hue_fix(self):
        """Test Aorus X470 specific hue correction."""
        # Start with red color
        original_color = [255, 0, 0]
        corrected_color = aorus_x470_hue_fix(original_color)
        
        # Convert both to HSV for easier comparison
        original_hsv = rgb_to_hsv(original_color)
        corrected_hsv = rgb_to_hsv(corrected_color)
        
        # The hue should be shifted by approximately -60 degrees
        # Taking into account potential wraparound
        expected_hue = (original_hsv[0] - 60) % 360
        assert abs(corrected_hsv[0] - expected_hue) <= 1
        
        # Saturation and value should remain unchanged
        assert corrected_hsv[1] == original_hsv[1]
        assert corrected_hsv[2] == original_hsv[2]
        
        # Test other base colors (green, blue)
        green = [0, 255, 0]
        blue = [0, 0, 255]
        
        # Check that each color gets properly adjusted
        assert aorus_x470_hue_fix(green) != green
        assert aorus_x470_hue_fix(blue) != blue
        
        # Test edge cases
        assert aorus_x470_hue_fix([]) == []  # Empty list
        assert aorus_x470_hue_fix([10]) == [10]  # Too short list
        assert aorus_x470_hue_fix(None) is None  # None input
    
    def test_asus_aura_brightness_correction(self):
        """Test Asus Aura specific brightness correction."""
        # Start with bright red color
        original_color = [255, 0, 0]
        corrected_color = asus_aura_brightness_correction(original_color)
        
        # Convert both to HSV for easier comparison
        original_hsv = rgb_to_hsv(original_color)
        corrected_hsv = rgb_to_hsv(corrected_color)
        
        # The brightness should be reduced by default factor (0.8)
        # Value in HSV represents brightness
        assert corrected_hsv[2] < original_hsv[2]
        expected_value = original_hsv[2] * 0.8
        assert abs(corrected_hsv[2] - expected_value) <= 1
        
        # Hue and saturation should remain unchanged
        assert corrected_hsv[0] == original_hsv[0]
        assert corrected_hsv[1] == original_hsv[1]
        
        # Test with custom brightness factor
        custom_factor = 0.5
        custom_corrected = asus_aura_brightness_correction(original_color, custom_factor)
        custom_hsv = rgb_to_hsv(custom_corrected)
        
        # Verify custom brightness reduction
        expected_custom_value = original_hsv[2] * custom_factor
        assert abs(custom_hsv[2] - expected_custom_value) <= 1
        
        # Test with brightness factor > 1 (brighter)
        bright_factor = 1.2
        bright_corrected = asus_aura_brightness_correction(original_color, bright_factor)
        bright_hsv = rgb_to_hsv(bright_corrected)
        
        # Should be brighter, but capped at 100
        assert bright_hsv[2] >= original_hsv[2]
        assert bright_hsv[2] <= 100
    
    def test_corsair_icue_color_mapping(self):
        """Test Corsair iCUE color mapping."""
        # Start with red color
        original_color = [255, 0, 0]
        mapped_color = corsair_icue_color_mapping(original_color)
        
        # Convert both to HSV for easier comparison
        original_hsv = rgb_to_hsv(original_color)
        mapped_hsv = rgb_to_hsv(mapped_color)
        
        # The hue should be shifted slightly
        assert mapped_hsv[0] != original_hsv[0]
        
        # Saturation should be increased (but capped at 100)
        expected_saturation = min(100, original_hsv[1] * 1.1)
        assert abs(mapped_hsv[1] - expected_saturation) <= 1
        
        # Value should remain unchanged
        assert mapped_hsv[2] == original_hsv[2]
        
        # Test with other colors
        other_colors = [
            [0, 255, 0],  # Green
            [0, 0, 255],  # Blue
            [255, 255, 0]  # Yellow
        ]
        
        for color in other_colors:
            mapped = corsair_icue_color_mapping(color)
            assert mapped != color  # Should be adjusted
        
        # Test with already saturated color (saturation = 100)
        saturated_color = hsv_to_rgb([120, 100, 100])  # Pure green, fully saturated
        saturated_mapped = corsair_icue_color_mapping(saturated_color)
        saturated_mapped_hsv = rgb_to_hsv(saturated_mapped)
        assert saturated_mapped_hsv[1] == 100  # Should still be 100 (capped)
    
    def test_msi_mystic_light_correction(self):
        """Test MSI Mystic Light color correction."""
        # MSI correction adjusts red and blue components
        original_color = [200, 100, 200]  # Purple-ish
        corrected_color = msi_mystic_light_correction(original_color)
        
        # Red should be increased, blue decreased
        assert corrected_color[0] > original_color[0]  # Red boosted
        assert corrected_color[2] < original_color[2]  # Blue reduced
        assert corrected_color[1] == original_color[1]  # Green unchanged
        
        # Check specific adjustments
        expected_red = min(255, int(original_color[0] * 1.1))
        expected_blue = int(original_color[2] * 0.9)
        
        assert corrected_color[0] == expected_red
        assert corrected_color[2] == expected_blue
        
        # Test with maximum values to ensure no overflow
        max_color = [255, 100, 255]
        max_corrected = msi_mystic_light_correction(max_color)
        
        assert max_corrected[0] == 255  # Should remain capped at 255
        assert max_corrected[2] < 255  # Blue should be reduced
        
        # Test with minimum values
        min_color = [0, 0, 0]
        min_corrected = msi_mystic_light_correction(min_color)
        assert min_corrected == [0, 0, 0]  # Should remain at minimum
    
    def test_asrock_polychrome_correction(self):
        """Test ASRock Polychrome color correction."""
        # ASRock shifts hue and may reduce brightness for bright colors
        original_color = [255, 0, 0]  # Bright red
        corrected_color = asrock_polychrome_correction(original_color)
        
        # Convert to HSV for comparison
        original_hsv = rgb_to_hsv(original_color)
        corrected_hsv = rgb_to_hsv(corrected_color)
        
        # Hue should be shifted
        expected_hue = (original_hsv[0] + 15) % 360
        assert abs(corrected_hsv[0] - expected_hue) <= 1
        
        # Test with a very bright color to check brightness adjustment
        bright_color = [200, 200, 200]  # Bright gray
        bright_corrected = asrock_polychrome_correction(bright_color)
        bright_corrected_hsv = rgb_to_hsv(bright_corrected)
        
        # Should have reduced brightness
        assert bright_corrected_hsv[2] < rgb_to_hsv(bright_color)[2]
        
        # Test with a color just at the brightness threshold
        threshold_color = hsv_to_rgb([0, 0, 81])  # Just above 80% brightness
        threshold_corrected = asrock_polychrome_correction(threshold_color)
        threshold_corrected_hsv = rgb_to_hsv(threshold_corrected)
        
        # Should be slightly reduced
        assert threshold_corrected_hsv[2] < 81
        
        # Test with a color below the brightness threshold
        below_threshold = hsv_to_rgb([0, 0, 75])  # Below 80% brightness
        below_corrected = asrock_polychrome_correction(below_threshold)
        below_corrected_hsv = rgb_to_hsv(below_corrected)
        
        # Brightness should remain unchanged (only hue shift applied)
        assert abs(below_corrected_hsv[2] - 75) <= 1
    
    def test_nzxt_cam_correction(self):
        """Test NZXT CAM color correction."""
        # NZXT adjusts saturation for very high or low saturated colors
        
        # Test with highly saturated color
        high_sat_color = [255, 0, 0]  # Fully saturated red
        high_sat_corrected = nzxt_cam_correction(high_sat_color)
        
        high_sat_hsv = rgb_to_hsv(high_sat_color)
        corrected_high_sat_hsv = rgb_to_hsv(high_sat_corrected)
        
        # Saturation should be capped at 90% (allow small floating point differences)
        assert abs(corrected_high_sat_hsv[1] - 90) < 0.2
        
        # Test with low saturation color
        low_sat_color = [128, 118, 120]  # Low saturation color
        low_sat_hsv = rgb_to_hsv(low_sat_color)
        
        # Only test if the original saturation is in the range we're adjusting
        if 0 < low_sat_hsv[1] < 20:
            low_sat_corrected = nzxt_cam_correction(low_sat_color)
            corrected_low_sat_hsv = rgb_to_hsv(low_sat_corrected)
            
            # Saturation should be boosted to 20% (allow small floating point differences)
            assert abs(corrected_low_sat_hsv[1] - 20) < 0.5
            # Hue should remain the same (allow small floating point differences)
            assert abs(corrected_low_sat_hsv[0] - low_sat_hsv[0]) < 0.5
            assert corrected_low_sat_hsv[2] == low_sat_hsv[2]  # Value unchanged
        
        # Create a guaranteed low saturation color for testing
        forced_low_sat = hsv_to_rgb([180, 10, 50])  # Low saturation color
        forced_corrected = nzxt_cam_correction(forced_low_sat)
        forced_corrected_hsv = rgb_to_hsv(forced_corrected)
        
        # Should boost saturation to 20% (allow small floating point differences)
        assert abs(forced_corrected_hsv[1] - 20) < 0.5
        
        # Test with zero saturation (grayscale)
        gray_color = [128, 128, 128]  # Pure gray (zero saturation)
        gray_hsv = rgb_to_hsv(gray_color)
        assert gray_hsv[1] == 0  # Confirm zero saturation
        
        gray_corrected = nzxt_cam_correction(gray_color)
        gray_corrected_hsv = rgb_to_hsv(gray_corrected)
        
        # Zero saturation should remain unchanged
        assert gray_corrected_hsv[1] == 0


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
        temp_diffs = [temps[i+1] - temps[i] for i in range(len(temps)-1)]
        
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
        same_temp_custom = temperature_to_color(50, min_temp=50, max_temp=50, 
                                              cool_color=green, warm_color=yellow)
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


class TestColorApplications:
    """Tests for applying color transformations to hardware."""
    
    def test_apply_hardware_specific_correction(self):
        """Test applying hardware-specific corrections."""
        # Test with each supported hardware type
        test_color = [255, 100, 50]  # Orange-red
        
        hardware_types = ['aorus', 'asus', 'corsair', 'msi', 'asrock', 'nzxt', 'generic']
        
        for hw_type in hardware_types:
            corrected = apply_hardware_specific_correction(test_color, hw_type)
            
            # Each hardware type should apply its specific correction
            if hw_type == 'generic':
                # Generic should return original color
                assert corrected == test_color
            else:
                # Others should modify the color
                assert corrected != test_color
        
        # Test with unknown hardware type (should return original)
        assert apply_hardware_specific_correction(test_color, 'unknown') == test_color
        
        # Test with mixed case
        mixed_case = apply_hardware_specific_correction(test_color, 'AsUs')
        lower_case = apply_hardware_specific_correction(test_color, 'asus')
        assert mixed_case == lower_case  # Case insensitive
        
        # Test with invalid color
        assert apply_hardware_specific_correction([], 'asus') == []
        assert apply_hardware_specific_correction(None, 'asus') is None