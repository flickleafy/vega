"""
Vega Common Library

This package provides shared utilities and functions used across the different
components of the Vega project (rootspace, userspace, gateway, and client).

The library follows clean architecture principles and implements best practices
for error handling, performance optimization, and code reusability.

Available modules:
- files_manipulation: File handling utilities with robust error handling
- list_process: List manipulation and processing utilities
- datetime_utils: Date and time formatting and manipulation functions
- sub_process: Shell command execution with various security and error handling options
- color_utils: Color conversion and manipulation functions
- temperature_utils: Temperature conversion and calculation utilities
- sliding_window: Advanced sliding window implementation for time-series data

Usage:
    # Import specific utilities
    from vega_common.utils.files_manipulation import read_file, write_file
    from vega_common.utils.list_process import list_average
    from vega_common.utils.sub_process import run_cmd
    from vega_common.utils.datetime_utils import get_current_time
    from vega_common.utils.color_utils import rgb_to_hsv, hsv_to_rgb
    from vega_common.utils.temperature_utils import estimate_cpu_from_liquid_temp
    from vega_common.utils.sliding_window import SlidingWindow
    
    # Or use shortcuts from the root package
    from vega_common import read_file, list_average, get_current_time, rgb_to_hsv, SlidingWindow
"""

# Import common utilities for easier access
from vega_common.utils.files_manipulation import read_file, write_file, safe_open, ensure_directory_exists
from vega_common.utils.list_process import list_average, remove_first_add_last, safe_get, create_sliding_window
from vega_common.utils.sub_process import run_cmd, run_cmd_with_status, run_cmd_sudo
from vega_common.utils.datetime_utils import get_current_time, get_timestamp, format_duration, is_older_than
from vega_common.utils.color_utils import (
    rgb_to_hsv, hsv_to_rgb, rgb_to_hex, hex_to_rgb,
    shift_hue, adjust_brightness, normalize_color_value,
    normalize_rgb_values, colors_are_similar, calculate_color_signature,
    calculate_color_distance, rgb_to_rgbcolor, handle_extreme_hsv
)
from vega_common.utils.temperature_utils import (
    celsius_to_fahrenheit, fahrenheit_to_celsius,
    estimate_cpu_from_liquid_temp, calculate_safe_fan_speed,
    cpu_temp_to_fan_speed, gpu_temp_to_fan_speed
)
# Import the new SlidingWindow class
from vega_common.utils.sliding_window import SlidingWindow, NumericSlidingWindow
# Import process utilities
from vega_common.utils.process_utils import get_process_list, similar_string_list

__version__ = '0.1.0'
__author__ = 'Vega Team'

# Add new utils to __all__ if defining it, otherwise they are exported by default