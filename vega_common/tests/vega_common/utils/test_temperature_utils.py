"""
Unit tests for the temperature_utils module.

Tests all functions in the vega_common.utils.temperature_utils module to ensure
they behave as expected across different contexts and edge cases.
"""
import pytest
from vega_common.utils.temperature_utils import (
    celsius_to_fahrenheit, 
    fahrenheit_to_celsius,
    estimate_cpu_from_liquid_temp,
    calculate_safe_fan_speed,
    gpu_temp_to_fan_speed,
    cpu_temp_to_fan_speed
)


class TestTemperatureConversions:
    """Tests for temperature conversion functions."""
    
    def test_celsius_to_fahrenheit(self):
        """Test celsius_to_fahrenheit with various values."""
        assert celsius_to_fahrenheit(0) == 32.0
        assert celsius_to_fahrenheit(100) == 212.0
        assert celsius_to_fahrenheit(-40) == -40.0
        assert celsius_to_fahrenheit(37) == 98.6
        assert abs(celsius_to_fahrenheit(20) - 68.0) < 0.001
    
    def test_fahrenheit_to_celsius(self):
        """Test fahrenheit_to_celsius with various values."""
        assert fahrenheit_to_celsius(32) == 0.0
        assert fahrenheit_to_celsius(212) == 100.0
        assert fahrenheit_to_celsius(-40) == -40.0
        assert abs(fahrenheit_to_celsius(98.6) - 37.0) < 0.001
        assert abs(fahrenheit_to_celsius(68) - 20.0) < 0.001


class TestCpuTempEstimation:
    """Tests for CPU temperature estimation function."""
    
    def test_estimate_cpu_from_liquid_temp_mode0(self):
        """Test estimate_cpu_from_liquid_temp with mode 0."""
        # Test with different temperature ranges in mode 0
        assert estimate_cpu_from_liquid_temp(25, mode=0) == 40.0
        assert estimate_cpu_from_liquid_temp(35, mode=0) == 35 + (15.0 * 1.2)
        assert estimate_cpu_from_liquid_temp(45, mode=0) == 45 + (15.0 * 1.4)
        
        # Test with custom offset and scaling factor
        assert estimate_cpu_from_liquid_temp(45, offset=10.0, scaling_factor=1.5, mode=0) == 45 + (10.0 * 1.5)
        
    def test_estimate_cpu_from_liquid_temp_mode1(self):
        """Test estimate_cpu_from_liquid_temp with mode 1."""
        # Test the empirical formula in mode 1
        expected = (-727.5 + (30 * 35)) / 7.5
        assert estimate_cpu_from_liquid_temp(35, mode=1) == expected
        
        # Test another temperature case
        expected2 = (-727.5 + (30 * 40)) / 7.5
        assert estimate_cpu_from_liquid_temp(40, mode=1) == expected2
        
    def test_estimate_cpu_from_liquid_temp_invalid_mode(self):
        """Test estimate_cpu_from_liquid_temp with an invalid mode defaults to mode 1."""
        # Invalid mode should default to mode 1 behavior
        expected = (-727.5 + (30 * 35)) / 7.5
        assert estimate_cpu_from_liquid_temp(35, mode=999) == expected


class TestFanSpeedCalculations:
    """Tests for fan speed calculation functions."""
    
    def test_calculate_safe_fan_speed(self):
        """Test calculate_safe_fan_speed with various inputs."""
        # Test at minimum temperature
        assert calculate_safe_fan_speed(30.0) == 20
        
        # Test at maximum temperature
        assert calculate_safe_fan_speed(75.0) == 100
        
        # Test at middle temperature
        mid_temp = (30.0 + 75.0) / 2  # 52.5
        mid_speed = (20 + 100) / 2    # 60
        assert calculate_safe_fan_speed(mid_temp) == int(round(mid_speed))
        
        # Test with custom temperature and speed ranges
        assert calculate_safe_fan_speed(40.0, min_temp=30.0, max_temp=50.0, min_speed=0, max_speed=80) == 40
        
        # Test temperature below minimum (should clamp to min speed)
        assert calculate_safe_fan_speed(20.0) == 20
        
        # Test temperature above maximum (should clamp to max speed)
        assert calculate_safe_fan_speed(80.0) == 100
        
    def test_gpu_temp_to_fan_speed(self):
        """Test gpu_temp_to_fan_speed with various temperatures."""
        # Test formula: speed = round(((5 * temp) - 100) * 0.5)
        
        # For temp = 40, speed = round(((5 * 40) - 100) * 0.5) = round(50) = 50
        assert gpu_temp_to_fan_speed(40.0) == 50
        
        # Test with modifier
        # For temp = 40, modified_temp = 40 * 1.1 = 44
        # speed = round(((5 * 44) - 100) * 0.5) = round(60) = 60
        assert gpu_temp_to_fan_speed(40.0, modifier=0.1) == 60
        
        # Test temperature that would result in negative speed (should clamp to 0)
        assert gpu_temp_to_fan_speed(10.0) == 0
        
        # Test temperature that would result in speed > 100 (should clamp to 100)
        assert gpu_temp_to_fan_speed(70.0) == 100
        
    def test_cpu_temp_to_fan_speed(self):
        """Test cpu_temp_to_fan_speed with various temperatures."""
        # Test formula: speed = round((6 * temp) - 200)
        
        # For temp = 50, speed = round((6 * 50) - 200) = round(100) = 100
        assert cpu_temp_to_fan_speed(50.0) == 100
        
        # For temp = 40, speed = round((6 * 40) - 200) = round(40) = 40
        assert cpu_temp_to_fan_speed(40.0) == 40
        
        # Test temperature that would result in negative speed (should clamp to 0)
        assert cpu_temp_to_fan_speed(30.0) == 0
        
        # Test temperature that would result in speed > 100 (should clamp to 100)
        assert cpu_temp_to_fan_speed(60.0) == 100