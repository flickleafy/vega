"""
Temperature utilities for the Vega project.

This module provides common temperature operations used across Vega sub-projects.
"""
from typing import Union, Optional, List, Tuple


def celsius_to_fahrenheit(celsius: float) -> float:
    """
    Convert Celsius temperature to Fahrenheit.
    
    Args:
        celsius (float): Temperature in Celsius
        
    Returns:
        float: Temperature in Fahrenheit
    """
    return (celsius * 9/5) + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """
    Convert Fahrenheit temperature to Celsius.
    
    Args:
        fahrenheit (float): Temperature in Fahrenheit
        
    Returns:
        float: Temperature in Celsius
    """
    return (fahrenheit - 32) * 5/9


def estimate_cpu_from_liquid_temp(liquid_temp: float, offset: float = 15.0, scaling_factor: float = 1.4, mode: int = 1) -> float:
    """
    Estimate CPU temperature based on liquid cooling temperature.
    
    CPU temperature is typically higher than liquid temperature.
    This function provides an estimate based on empirical observations.
    
    Args:
        liquid_temp (float): Liquid cooling temperature in Celsius
        offset (float, optional): Base temperature difference. Defaults to 15.0.
        scaling_factor (float, optional): Scaling factor for higher temperatures. Defaults to 1.4.
        
    Returns:
        float: Estimated CPU temperature in Celsius
    """
    # For higher liquid temps, the difference between CPU and liquid increases
    if mode == 0:
      if liquid_temp < 30:
          return liquid_temp + offset
      elif liquid_temp < 40:
          return liquid_temp + (offset * 1.2)
      else:
          return liquid_temp + (offset * scaling_factor)
    elif mode == 1:
      return (-727.5 + (30 * liquid_temp)) / 7.5
    



def calculate_safe_fan_speed(temp: float, min_temp: float = 30.0, max_temp: float = 75.0, 
                             min_speed: int = 20, max_speed: int = 100) -> int:
    """
    Calculate fan speed based on temperature.
    
    Args:
        temp (float): Current temperature in Celsius
        min_temp (float, optional): Temperature at which to use minimum fan speed. Defaults to 30.0.
        max_temp (float, optional): Temperature at which to use maximum fan speed. Defaults to 75.0.
        min_speed (int, optional): Minimum fan speed percentage. Defaults to 20.
        max_speed (int, optional): Maximum fan speed percentage. Defaults to 100.
        
    Returns:
        int: Fan speed percentage (0-100)
    """
    # Clamp temperature to the range
    temp = max(min_temp, min(temp, max_temp))
    
    # Calculate the percentage between min_temp and max_temp
    temp_range = max_temp - min_temp
    temp_percentage = (temp - min_temp) / temp_range
    
    # Calculate fan speed
    speed_range = max_speed - min_speed
    speed = min_speed + (temp_percentage * speed_range)
    
    return int(round(speed))


def gpu_temp_to_fan_speed(temp: float, modifier: float = 0.0) -> int:
    """
    Convert GPU temperature to fan speed percentage using a custom formula.
    
    This function is specifically designed for GPU fan control with a 
    non-linear response curve that's more aggressive at higher temperatures.
    
    Args:
        temp (float): GPU temperature in Celsius
        modifier (float, optional): Adjustment factor to customize the curve. 
                                   Positive values make the response more aggressive.
                                   Defaults to 0.0.
    
    Returns:
        int: Fan speed percentage (0-100)
    """
    # Apply the temperature modifier
    adjusted_temp = temp * (1 + modifier)
    
    # Calculate speed using custom formula
    # This formula creates a more aggressive curve than linear interpolation
    speed = round(((5 * adjusted_temp) - 100) * 0.5)
    
    # Ensure speed is within valid range
    speed = min(100, max(0, speed))
    
    return speed


def cpu_temp_to_fan_speed(temp: float) -> int:
    """
    Convert CPU temperature to watercooler fan speed percentage.
    
    This function is specifically designed for CPU watercooling systems 
    and uses a custom formula optimized for liquid cooling radiators.
    
    Args:
        temp (float): CPU or liquid temperature in Celsius
        
    Returns:
        int: Fan speed percentage (0-100)
    """
    # Calculate speed using custom formula for CPU cooling
    # This formula provides a steeper curve than the GPU formula
    speed = round((6 * temp) - 200)
    
    # Ensure speed is within valid range
    speed = min(100, max(0, speed))
    
    return speed