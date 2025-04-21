"""
Color utilities for the rootspace component.

This module re-exports color manipulation functions from the vega_common library
to maintain backward compatibility while reducing code duplication.
"""

from vega_common.utils.color_utils import (
    rgb_to_hsv,
    hsv_to_rgb,
    rgb_to_hex,
    hex_to_rgb,
    shift_hue,
    adjust_brightness,
    normalize_color_value,
    colors_are_similar,
    calculate_color_signature,
    calculate_color_distance,
    normalize_rgb_values,
    rgb_to_rgbcolor,
    handle_extreme_hsv,
)

# These functions are now imported directly from vega_common.utils.color_utils
# Keeping this file for backward compatibility
