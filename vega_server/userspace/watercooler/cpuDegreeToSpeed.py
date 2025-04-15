"""
Temperature to fan speed conversion functions for CPU watercooling.

This module provides functionality to convert CPU/liquid temperature readings to 
appropriate fan speed settings for optimal cooling.
"""
from vega_common.utils.temperature_utils import cpu_temp_to_fan_speed as common_cpu_temp_to_fan_speed


def degree_to_speed(degree: float) -> int:
    """
    Convert CPU/liquid temperature to fan speed percentage.
    
    Args:
        degree (float): CPU or liquid temperature in degrees Celsius
        
    Returns:
        int: Fan speed percentage (0-100)
    """
    return common_cpu_temp_to_fan_speed(degree)
