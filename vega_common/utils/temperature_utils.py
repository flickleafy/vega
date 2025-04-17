"""
Temperature utilities for the Vega project.

This module provides common temperature operations used across Vega sub-projects,
including temperature conversions, estimations, and fan speed calculations.
"""
from typing import Union, Optional, List, Tuple
import statistics
from vega_common.utils.sliding_window import SlidingWindow
from vega_common.utils.list_process import create_sliding_window


def celsius_to_fahrenheit(celsius: float) -> float:
    """
    Convert temperature from Celsius to Fahrenheit.
    
    Args:
        celsius (float): Temperature in degrees Celsius
        
    Returns:
        float: Temperature in degrees Fahrenheit
    """
    return (celsius * 9/5) + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """
    Convert temperature from Fahrenheit to Celsius.
    
    Args:
        fahrenheit (float): Temperature in degrees Fahrenheit
        
    Returns:
        float: Temperature in degrees Celsius
    """
    return (fahrenheit - 32) * 5/9


def estimate_cpu_from_liquid_temp(
    liquid_temp: float, 
    offset: float = 15, 
    scaling_factor: float = 1.4, 
    mode: int = 1
) -> float:
    """
    Estimate CPU temperature based on liquid cooling temperature.
    
    CPU temperature is typically higher than liquid temperature.
    This function provides an estimate based on empirical observations.
    
    Args:
        liquid_temp (float): Liquid temperature in degrees Celsius
        offset (float, optional): Temperature offset in degrees. Default is 15.
        scaling_factor (float, optional): Scaling factor for dynamic offset. Default is 1.4.
        mode (int, optional): Estimation mode. 
            0: Scaled offset method
            1: Empirical formula method
            Default is 1.
            
    Returns:
        float: Estimated CPU temperature in degrees Celsius
    """
    # For higher liquid temps, the difference between CPU and liquid increases
    if mode == 0:
        # Scaled offset method
        if liquid_temp <= 30:
            # Low liquid temp: basic offset
            return liquid_temp + offset
        elif liquid_temp <= 40:
            # Medium liquid temp: slightly scaled offset
            return liquid_temp + (offset * 1.2)
        else:
            # High liquid temp: fully scaled offset
            return liquid_temp + (offset * scaling_factor)
    else:
        # Empirical formula method (derived from experimental data)
        # This formula estimates CPU temperature based on observed relationships
        # between liquid and CPU temperatures in typical water cooling setups
        return (-727.5 + (30 * liquid_temp)) / 7.5


def calculate_safe_fan_speed(
    temperature: float, 
    min_temp: float = 30, 
    max_temp: float = 75, 
    min_speed: int = 20, 
    max_speed: int = 100
) -> int:
    """
    Calculate an appropriate fan speed based on temperature.
    
    Uses linear interpolation between min_speed and max_speed based on 
    how temperature relates to min_temp and max_temp.
    
    Args:
        temperature (float): Current temperature in degrees Celsius
        min_temp (float, optional): Temperature at which fan should run at min_speed. Default is 30.
        max_temp (float, optional): Temperature at which fan should run at max_speed. Default is 75.
        min_speed (int, optional): Minimum fan speed percentage. Default is 20.
        max_speed (int, optional): Maximum fan speed percentage. Default is 100.
        
    Returns:
        int: Fan speed as percentage (0-100)
    """
    # Ensure proper ordering of min/max values
    actual_min_temp, actual_max_temp = min(min_temp, max_temp), max(min_temp, max_temp)
    actual_min_speed, actual_max_speed = min(min_speed, max_speed), max(min_speed, max_speed)
    
    # Handle special case where there's no temperature range
    if actual_min_temp == actual_max_temp:
        return actual_max_speed
    
    # Handle special case where there's no speed range
    if actual_min_speed == actual_max_speed:
        return actual_min_speed
    
    # Determine if we need to invert the speed mapping
    invert_mapping = (min_temp > max_temp) != (min_speed > max_speed)
    
    # Calculate normalized position in range (0.0 to 1.0)
    if temperature <= actual_min_temp:
        normalized = 0.0
    elif temperature >= actual_max_temp:
        normalized = 1.0
    else:
        normalized = (temperature - actual_min_temp) / (actual_max_temp - actual_min_temp)
    
    # Apply speed mapping with inversion if needed
    if invert_mapping:
        normalized = 1.0 - normalized
    
    # Calculate fan speed using linear interpolation
    fan_speed = actual_min_speed + normalized * (actual_max_speed - actual_min_speed)
    
    # Round to nearest integer
    return int(round(fan_speed))


def gpu_temp_to_fan_speed(degree: float, modifier: float = 0) -> int:
    """
    Convert GPU temperature to fan speed percentage using a custom formula.
    
    This function is specifically designed for GPU fan control with a 
    non-linear response curve that's more aggressive at higher temperatures.
    
    Args:
        degree (float): GPU temperature in degrees Celsius
        modifier (float, optional): Adjustment factor for fan curve. Default is 0.
            When positive, applies as a multiplier: degree * (1 + modifier)
        
    Returns:
        int: Fan speed percentage (0-100)
    """
    # Apply modifier as a multiplicative factor (temp * (1 + modifier))
    effective_temp = degree * (1 + modifier) if modifier > 0 else degree + modifier * 20
    
    raw_percentage = ((5 * effective_temp) - 100) / 2
    
    # Clamp the result to 0-100 range
    if raw_percentage <= 0:
        return 0
    elif raw_percentage >= 100:
        return 100
    else:
        return round(raw_percentage)


def cpu_temp_to_fan_speed(degree: float) -> int:
    """
    Convert CPU temperature to fan speed percentage.
    
    Implements a fan curve specifically designed for CPU cooling needs.
    CPU fans typically need to respond faster to temperature changes
    than GPU fans, hence the different curve formula.
    
    Args:
        degree (float): CPU temperature in degrees Celsius
        
    Returns:
        int: Fan speed percentage (0-100)
    """
    # Formula: (6 * temp) - 200
    # This provides:
    # - 0% at 33.33°C or below
    # - 50% at ~41.67°C
    # - 100% at 50°C and above
    
    raw_percentage = (6 * degree) - 200
    
    # Clamp the result to 0-100 range
    if raw_percentage <= 0:
        return 0
    elif raw_percentage >= 100:
        return 100
    else:
        return round(raw_percentage)
    
    
    
def normalize_temperature(temp: float, min_temp: float = 0, max_temp: float = 100) -> float:
    """
    Normalize temperature value to be within the specified range.
    
    Args:
        temp (float): Temperature to normalize
        min_temp (float, optional): Minimum allowed temperature. Defaults to 0.
        max_temp (float, optional): Maximum allowed temperature. Defaults to 100.
        
    Returns:
        float: Normalized temperature value
    """
    return max(min_temp, min(max_temp, temp))


def average_temperatures(temperatures: List[float], discard_outliers: bool = False) -> float:
    """
    Calculate the average of a list of temperature values.
    
    Args:
        temperatures (List[float]): List of temperature values
        discard_outliers (bool, optional): Whether to discard outliers before averaging. 
                                        Defaults to False.
        
    Returns:
        float: Average temperature value
        
    Raises:
        ValueError: If the input list is empty
    """
    if not temperatures:
        raise ValueError("Cannot calculate average of an empty list")
    
    if discard_outliers and len(temperatures) > 3:
        # Remove outliers using the IQR method
        temperatures_sorted = sorted(temperatures)
        q1_idx = len(temperatures) // 4
        q3_idx = (len(temperatures) * 3) // 4
        q1 = temperatures_sorted[q1_idx]
        q3 = temperatures_sorted[q3_idx]
        iqr = q3 - q1
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        
        filtered_temps = [t for t in temperatures if lower_bound <= t <= upper_bound]
        if filtered_temps:  # Make sure we didn't filter everything
            return sum(filtered_temps) / len(filtered_temps)
    
    return sum(temperatures) / len(temperatures)


def calculate_temperature_trend(
    recent_temps: List[float], 
    window_size: int = 5
) -> Tuple[float, str]:
    """
    Calculate the temperature trend based on recent temperature readings.
    
    Args:
        recent_temps (List[float]): List of recent temperature readings
        window_size (int, optional): Size of the window to consider for trend analysis.
                                   Defaults to 5.
        
    Returns:
        Tuple[float, str]: A tuple containing:
            - The rate of change per sample (degrees per sample)
            - A string indicating the trend direction: "rising", "falling", or "stable"
    """
    if len(recent_temps) < 2:
        return 0.0, "stable"
    
    # Use only the last 'window_size' samples
    temps_to_analyze = recent_temps[-window_size:] if len(recent_temps) > window_size else recent_temps
    
    # Simple linear regression to find trend
    n = len(temps_to_analyze)
    indices = list(range(n))
    
    # Calculate means
    mean_x = sum(indices) / n
    mean_y = sum(temps_to_analyze) / n
    
    # Calculate slope using least squares method
    numerator = sum((i - mean_x) * (t - mean_y) for i, t in enumerate(temps_to_analyze))
    denominator = sum((i - mean_x) ** 2 for i in indices)
    
    # Avoid division by zero
    if denominator == 0:
        return 0.0, "stable"
        
    slope = numerator / denominator
    
    # Determine trend direction
    if abs(slope) < 0.2:  # Threshold for "stable" - may need adjustment
        trend = "stable"
    elif slope > 0:
        trend = "rising"
    else:
        trend = "falling"
        
    return slope, trend


def create_temperature_window(size: int = 10, initial_value: float = 0) -> SlidingWindow:
    """
    Create a sliding window specifically for temperature values.
    
    Args:
        size (int, optional): Size of the window. Defaults to 10.
        initial_value (float, optional): Initial value to fill the window. Defaults to 0.
        
    Returns:
        SlidingWindow: A sliding window configured for temperature values
    """
    # Use the actual SlidingWindow class instead of a list
    from vega_common.utils.sliding_window import NumericSlidingWindow
    
    # Create a numeric sliding window specifically designed for temperature values
    return NumericSlidingWindow(capacity=size, default_value=initial_value)


def temperature_within_range(
    temp: float, 
    target: float, 
    tolerance: float = 2.0
) -> bool:
    """
    Check if a temperature is within a specified range of a target value.
    
    Args:
        temp (float): The temperature to check
        target (float): The target temperature
        tolerance (float, optional): The allowed deviation from target. Defaults to 2.0 degrees.
        
    Returns:
        bool: True if the temperature is within the tolerance range, False otherwise
    """
    return abs(temp - target) <= tolerance

def classify_temperature(
    temp: float, 
    ranges: List[Tuple[float, float, str]] = None
) -> str:
    """
    Classify a temperature into a named range.
    
    Args:
        temp (float): Temperature to classify
        ranges (List[Tuple[float, float, str]], optional): List of (min, max, label) tuples.
                                                          Defaults to a standard set of ranges.
        
    Returns:
        str: Label for the temperature range, or "unknown" if not in any defined range
    """
    if ranges is None:
        # Default ranges: [(min_temp, max_temp, label)]
        ranges = [
            (0, 30, "cool"),
            (30, 45, "normal"),
            (45, 60, "warm"),
            (60, 80, "hot"),
            (80, float('inf'), "critical")
        ]
    
    for min_temp, max_temp, label in ranges:
        if min_temp <= temp < max_temp:
            return label
            
    return "unknown"


