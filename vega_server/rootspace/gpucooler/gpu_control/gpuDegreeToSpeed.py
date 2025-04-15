"""
Temperature to fan speed conversion functions for GPU cooling.

This module provides functionality to convert GPU temperature readings to 
appropriate fan speed settings for optimal cooling.
"""
from vega_common.utils.temperature_utils import gpu_temp_to_fan_speed as common_gpu_temp_to_fan_speed


def degree_to_speed(degree, modifier):
    """
    Convert GPU temperature to fan speed percentage.
    
    Args:
        degree (float): GPU temperature in degrees Celsius
        modifier (float): Adjustment factor for the fan curve
        
    Returns:
        int: Fan speed percentage (0-100)
    """
    return common_gpu_temp_to_fan_speed(degree, modifier)
