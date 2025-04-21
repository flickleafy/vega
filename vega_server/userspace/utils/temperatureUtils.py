"""
Temperature utilities for the userspace component.

This module re-exports temperature manipulation functions from the vega_common library
to maintain backward compatibility while reducing code duplication.
"""

from vega_common.utils.temperature_utils import (
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
    estimate_cpu_from_liquid_temp,
    calculate_safe_fan_speed,
    cpu_temp_to_fan_speed,
    gpu_temp_to_fan_speed,
)

# These functions are now imported directly from vega_common.utils.temperature_utils
# Keeping this file for backward compatibility
