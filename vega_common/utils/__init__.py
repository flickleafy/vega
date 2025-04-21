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
    handle_extreme_hsv,
)

from vega_common.utils.hardware_rgb_profiles import (
    aorus_x470_hue_fix,
    asus_aura_brightness_correction,
    corsair_icue_color_mapping,
    msi_mystic_light_correction,
    asrock_polychrome_correction,
    nzxt_cam_correction,
    apply_hardware_specific_correction,
)

from vega_common.utils.color_gradient_utils import (
    create_color_gradient,
    create_color_gradient_cielch,
    create_rainbow_gradient,
    create_temperature_gradient,
    get_temperature_color,
    temperature_to_color,
    _map_to_srgb_gamut,
    _lch_to_rgb_norm,
    _is_rgb_in_gamut,
)

# Re-export list processing utilities
from vega_common.utils.list_process import (
    list_average,
    remove_first_add_last,
    safe_get,
    create_sliding_window,
)

# Re-export sliding window implementations
from vega_common.utils.sliding_window import SlidingWindow, NumericSlidingWindow

# Re-export process utilities
from vega_common.utils.process_utils import get_process_list, similar_string_list
