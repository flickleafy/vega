"""
Unit tests for the color_utils module.

Tests all functions in the vega_common.utils.color_utils module to ensure
they behave as expected across different contexts and edge cases.
"""
import pytest
from vega_common.utils.color_utils import (
    rgb_to_hsv,
    hsv_to_rgb,
    rgb_to_hex,
    hex_to_rgb,
    shift_hue,
    adjust_brightness,
    normalize_color_value
)


class TestColorConversions:
    """Tests for color conversion functions."""
    
    def test_rgb_to_hsv(self):
        """Test rgb_to_hsv with various RGB colors."""
        # Test red
        rgb = [255, 0, 0]
        hsv = rgb_to_hsv(rgb)
        assert hsv[0] == 0  # Hue for red is 0
        assert hsv[1] == 100  # Full saturation
        assert hsv[2] == 100  # Full value
        
        # Test green
        rgb = [0, 255, 0]
        hsv = rgb_to_hsv(rgb)
        assert hsv[0] == 120  # Hue for green is 120
        assert hsv[1] == 100  # Full saturation
        assert hsv[2] == 100  # Full value
        
        # Test blue
        rgb = [0, 0, 255]
        hsv = rgb_to_hsv(rgb)
        assert hsv[0] == 240  # Hue for blue is 240
        assert hsv[1] == 100  # Full saturation
        assert hsv[2] == 100  # Full value
        
        # Test black
        rgb = [0, 0, 0]
        hsv = rgb_to_hsv(rgb)
        assert hsv[1] == 0  # No saturation
        assert hsv[2] == 0  # No value (black)
        
        # Test white
        rgb = [255, 255, 255]
        hsv = rgb_to_hsv(rgb)
        assert hsv[1] == 0  # No saturation
        assert hsv[2] == 100  # Full value

        # Test medium gray
        rgb = [128, 128, 128]
        hsv = rgb_to_hsv(rgb)
        assert hsv[1] == 0  # No saturation
        assert abs(hsv[2] - 50) <= 1  # Half value (allowing small rounding error)
    
    def test_hsv_to_rgb(self):
        """Test hsv_to_rgb with various HSV colors."""
        # Test red
        hsv = [0, 100, 100]
        rgb = hsv_to_rgb(hsv)
        assert rgb[0] == 255
        assert rgb[1] == 0
        assert rgb[2] == 0
        
        # Test green
        hsv = [120, 100, 100]
        rgb = hsv_to_rgb(hsv)
        assert rgb[0] == 0
        assert rgb[1] == 255
        assert rgb[2] == 0
        
        # Test blue
        hsv = [240, 100, 100]
        rgb = hsv_to_rgb(hsv)
        assert rgb[0] == 0
        assert rgb[1] == 0
        assert rgb[2] == 255
        
        # Test black
        hsv = [0, 0, 0]
        rgb = hsv_to_rgb(hsv)
        assert rgb[0] == 0
        assert rgb[1] == 0
        assert rgb[2] == 0
        
        # Test white
        hsv = [0, 0, 100]
        rgb = hsv_to_rgb(hsv)
        assert rgb[0] == 255
        assert rgb[1] == 255
        assert rgb[2] == 255
    
    def test_rgb_to_hex(self):
        """Test rgb_to_hex with various RGB colors."""
        # Test red
        rgb = [255, 0, 0]
        hex_color = rgb_to_hex(rgb[0], rgb[1], rgb[2])
        assert hex_color == "ff0000"
        
        # Test green
        rgb = [0, 255, 0]
        hex_color = rgb_to_hex(rgb[0], rgb[1], rgb[2])
        assert hex_color == "00ff00"
        
        # Test blue
        rgb = [0, 0, 255]
        hex_color = rgb_to_hex(rgb[0], rgb[1], rgb[2])
        assert hex_color == "0000ff"
        
        # Test black
        rgb = [0, 0, 0]
        hex_color = rgb_to_hex(rgb[0], rgb[1], rgb[2])
        assert hex_color == "000000"
        
        # Test white
        rgb = [255, 255, 255]
        hex_color = rgb_to_hex(rgb[0], rgb[1], rgb[2])
        assert hex_color == "ffffff"
        
        # Test values less than 16 (single digit in hex) to ensure padding
        rgb = [10, 10, 10]
        hex_color = rgb_to_hex(rgb[0], rgb[1], rgb[2])
        assert hex_color == "0a0a0a"
    
    def test_hex_to_rgb(self):
        """Test hex_to_rgb with various hex colors."""
        # Test red
        hex_color = "ff0000"
        rgb = hex_to_rgb(hex_color)
        assert rgb[0] == 255
        assert rgb[1] == 0
        assert rgb[2] == 0
        
        # Test green
        hex_color = "00ff00"
        rgb = hex_to_rgb(hex_color)
        assert rgb[0] == 0
        assert rgb[1] == 255
        assert rgb[2] == 0
        
        # Test blue
        hex_color = "0000ff"
        rgb = hex_to_rgb(hex_color)
        assert rgb[0] == 0
        assert rgb[1] == 0
        assert rgb[2] == 255
        
        # Test with # prefix
        hex_color = "#ff0000"
        rgb = hex_to_rgb(hex_color)
        assert rgb[0] == 255
        assert rgb[1] == 0
        assert rgb[2] == 0
        
        # Test with 3-character hex
        hex_color = "#f00"
        rgb = hex_to_rgb(hex_color)
        assert rgb[0] == 255
        assert rgb[1] == 0
        assert rgb[2] == 0
        
        # Test with uppercase hex
        hex_color = "00FF00"
        rgb = hex_to_rgb(hex_color)
        assert rgb[0] == 0
        assert rgb[1] == 255
        assert rgb[2] == 0


class TestColorManipulation:
    """Tests for color manipulation functions."""
    
    def test_shift_hue(self):
        """Test shift_hue with various shift values."""
        # Test positive shift within 360
        hsv = [120, 100, 100]  # Green
        shifted = shift_hue(hsv.copy(), 60)
        assert shifted[0] == 60  # Should become yellow (120 - 60 = 60)
        assert shifted[1] == hsv[1]  # Saturation unchanged
        assert shifted[2] == hsv[2]  # Value unchanged
        
        # Test negative shift
        hsv = [120, 100, 100]  # Green
        shifted = shift_hue(hsv.copy(), -120)
        assert shifted[0] == 240  # Should become blue (360 - 120 = 240)
        
        # Test wrap-around (negative resultant hue)
        hsv = [30, 100, 100]  # Orange
        shifted = shift_hue(hsv.copy(), 60)
        assert shifted[0] == 330  # Should wrap to 330 (red-purple)
        
        # Test no shift
        hsv = [120, 100, 100]  # Green
        shifted = shift_hue(hsv.copy(), 0)
        assert shifted == hsv  # Should remain unchanged
        
        # Test preserves original list (returns new list)
        hsv = [120, 100, 100]  # Green
        original = hsv.copy()
        shifted = shift_hue(hsv, 60)
        assert hsv == original  # Original should be unchanged
    
    def test_adjust_brightness(self):
        """Test adjust_brightness with various adjustment values."""
        # Test increase brightness 
        hsv = [0, 100, 50]  # Medium-bright red
        adjusted = adjust_brightness(hsv.copy(), 25)
        assert adjusted[0] == hsv[0]  # Hue unchanged
        assert adjusted[1] == hsv[1]  # Saturation unchanged
        assert adjusted[2] == 75  # Value increased
        
        # Test decrease brightness
        hsv = [0, 100, 75]  # Bright red
        adjusted = adjust_brightness(hsv.copy(), -25)
        assert adjusted[2] == 50  # Value decreased
        
        # Test max brightness clamping
        hsv = [0, 100, 90]  # Very bright red
        adjusted = adjust_brightness(hsv.copy(), 20)
        assert adjusted[2] == 100  # Value clamped to 100
        
        # Test min brightness clamping
        hsv = [0, 100, 10]  # Very dark red
        adjusted = adjust_brightness(hsv.copy(), -20)
        assert adjusted[2] == 0  # Value clamped to 0
        
        # Test no change
        hsv = [0, 100, 50]  # Medium-bright red
        adjusted = adjust_brightness(hsv.copy(), 0)
        assert adjusted == hsv  # Should remain unchanged
        
        # Test preserves original list (returns new list)
        hsv = [0, 100, 50]  # Medium-bright red
        original = hsv.copy()
        adjusted = adjust_brightness(hsv, 25)
        assert hsv == original  # Original should be unchanged


class TestHelperFunctions:
    """Tests for helper utility functions."""
    
    def test_normalize_color_value(self):
        """Test normalize_color_value with various values and ranges."""
        # Test value within range
        assert normalize_color_value(128, 0, 255) == 128
        
        # Test value below minimum
        assert normalize_color_value(-10, 0, 255) == 0
        
        # Test value above maximum
        assert normalize_color_value(300, 0, 255) == 255
        
        # Test custom range
        assert normalize_color_value(75, 50, 100) == 75
        assert normalize_color_value(25, 50, 100) == 50
        assert normalize_color_value(150, 50, 100) == 100
        
        # Test with float values
        assert normalize_color_value(0.5, 0, 1.0) == 0.5
        assert normalize_color_value(-0.5, 0, 1.0) == 0.0
        assert normalize_color_value(1.5, 0, 1.0) == 1.0
        
        # Test same min and max
        assert normalize_color_value(10, 5, 5) == 5