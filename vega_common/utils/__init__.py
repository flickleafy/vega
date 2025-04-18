"""
Vega Common Utilities

This package provides shared utility functions and classes for the Vega project.
"""

# Re-export color utilities for easy access
from vega_common.utils.color_utils import (
    rgb_to_hsv,
    hsv_to_rgb,
    rgb_to_hex,
    hex_to_rgb,
    shift_hue,
    adjust_brightness,
    normalize_color_value,
    normalize_rgb_values,
    colors_are_similar,
    calculate_color_signature,
    calculate_color_distance,
    rgb_to_rgbcolor,
    handle_extreme_hsv
)

# Re-export list processing utilities
from vega_common.utils.list_process import (
    list_average,
    remove_first_add_last,
    safe_get,
    create_sliding_window
)

# Re-export sliding window implementations
from vega_common.utils.sliding_window import (
    SlidingWindow,
    NumericSlidingWindow
)

# Re-export process utilities
from vega_common.utils.process_utils import (
    get_process_list,
    similar_string_list
)