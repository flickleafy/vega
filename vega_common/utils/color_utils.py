"""
Color manipulation utilities for the Vega project.

This module provides common color manipulation operations used across Vega sub-projects.
"""
import colorsys
from typing import List, Tuple, Union

def rgb_to_hsv(array_rgb: List[int]) -> List[int]:
    """
    Convert RGB color values to HSV color space.
    
    Args:
        array_rgb (List[int]): RGB values as a list [r, g, b] with values from 0-255
        
    Returns:
        List[int]: HSV values as a list [h, s, v] with h in range 0-360, s and v in range 0-100
    """
    # input
    (r, g, b) = (array_rgb[0], array_rgb[1], array_rgb[2])
    # normalize
    (r, g, b) = (r / 255, g / 255, b / 255)
    # convert to hsv
    (h, s, v) = colorsys.rgb_to_hsv(r, g, b)
    # expand HSV range
    (h, s, v) = (int(h * 360), int(s * 100), int(v * 100))
    return [h, s, v]


def hsv_to_rgb(array_hsv: List[int]) -> List[int]:
    """
    Convert HSV color values to RGB color space.
    
    Args:
        array_hsv (List[int]): HSV values as a list [h, s, v] with h in range 0-360, s and v in range 0-100
        
    Returns:
        List[int]: RGB values as a list [r, g, b] with values from 0-255
    """
    # input
    (h, s, v) = (array_hsv[0], array_hsv[1], array_hsv[2])
    # normalize
    (h, s, v) = (h / 360, s / 100, v / 100)
    # convert to rgb
    (r, g, b) = colorsys.hsv_to_rgb(h, s, v)
    # expand RGB range
    (r, g, b) = (int(r * 255), int(g * 255), int(b * 255))
    return [r, g, b]


def shift_hue(array_hsv: List[int], shift: int) -> List[int]:
    """
    Shift the hue component of an HSV color.
    
    Args:
        array_hsv (List[int]): HSV values as a list [h, s, v] with h in range 0-360, s and v in range 0-100
        shift (int): Amount to shift the hue (in degrees)
        
    Returns:
        List[int]: HSV values with shifted hue as a list [h, s, v]
    """
    # position 0 is hue
    new_hue = array_hsv[0] - shift
    if new_hue < 0:
        new_hue = 360 - abs(new_hue)
    array_hsv[0] = new_hue % 360
    return array_hsv


def adjust_brightness(array_hsv: List[int], adjustment: int) -> List[int]:
    """
    Adjust the brightness (value) component of an HSV color.
    
    Args:
        array_hsv (List[int]): HSV values as a list [h, s, v] with h in range 0-360, s and v in range 0-100
        adjustment (int): Amount to adjust brightness (can be positive or negative)
        
    Returns:
        List[int]: HSV values with adjusted brightness as a list [h, s, v]
    """
    # position 2 is value (brightness)
    new_value = array_hsv[2] + adjustment
    array_hsv[2] = max(0, min(100, new_value))
    return array_hsv


def rgb_to_hex(red: int, green: int, blue: int) -> str:
    """
    Convert RGB values to hexadecimal color representation.
    
    Args:
        red (int): Red component (0-255)
        green (int): Green component (0-255)
        blue (int): Blue component (0-255)
        
    Returns:
        str: Hexadecimal color string without # prefix
    """
    red = format(max(0, min(255, red)), '02x')
    green = format(max(0, min(255, green)), '02x')
    blue = format(max(0, min(255, blue)), '02x')
    
    return f"{red}{green}{blue}"


def hex_to_rgb(hex_color: str) -> List[int]:
    """
    Convert hexadecimal color to RGB values.
    
    Args:
        hex_color (str): Hexadecimal color string (with or without # prefix)
        
    Returns:
        List[int]: RGB values as a list [r, g, b]
    """
    hex_color = hex_color.lstrip('#')
    
    return [
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16)
    ]


def normalize_color_value(color: int, min_value: int = 0, max_value: int = 255) -> int:
    """
    Ensure a color value is within the specified range.
    
    Args:
        color (int): Color value to normalize
        min_value (int): Minimum allowed value (default: 0)
        max_value (int): Maximum allowed value (default: 255)
        
    Returns:
        int: Normalized color value
    """
    return max(min_value, min(color, max_value))