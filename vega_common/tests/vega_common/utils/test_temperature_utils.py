"""
Unit tests for the temperature_utils module.

Tests all functions in the vega_common.utils.temperature_utils module to ensure
they behave as expected across different contexts and edge cases.
"""
import pytest
import math
from vega_common.utils.temperature_utils import (
    average_temperatures,
    calculate_temperature_trend,
    celsius_to_fahrenheit,
    classify_temperature,
    create_temperature_window,
    fahrenheit_to_celsius,
    estimate_cpu_from_liquid_temp,
    calculate_safe_fan_speed,
    gpu_temp_to_fan_speed,
    cpu_temp_to_fan_speed,
    normalize_temperature,
    temperature_within_range
)

class TestTemperatureConversions:
    """Tests for temperature conversion functions."""

    def test_celsius_to_fahrenheit(self):
        """Test celsius_to_fahrenheit with various values."""
        # Test common values
        assert celsius_to_fahrenheit(0) == 32.0  # Freezing point of water
        assert celsius_to_fahrenheit(100) == 212.0  # Boiling point of water
        assert celsius_to_fahrenheit(20) == 68.0  # Room temperature
        assert celsius_to_fahrenheit(-40) == -40.0  # Equal in both scales

        # Test with floating point values
        assert pytest.approx(celsius_to_fahrenheit(37.5), 0.001) == 99.5  # Body temperature
        assert pytest.approx(celsius_to_fahrenheit(-17.8), 0.001) == -0.04 # 0 degrees Fahrenheit (adjusting expected slightly for precision)

        # Test with very large and very small values
        assert celsius_to_fahrenheit(1000) == 1832.0
        assert celsius_to_fahrenheit(-273.15) == pytest.approx(-459.67)  # Absolute zero

    def test_fahrenheit_to_celsius(self):
        """Test fahrenheit_to_celsius with various values."""
        # Test common values
        assert fahrenheit_to_celsius(32) == 0.0  # Freezing point of water
        assert fahrenheit_to_celsius(212) == 100.0  # Boiling point of water
        assert fahrenheit_to_celsius(68) == 20.0  # Room temperature
        assert fahrenheit_to_celsius(-40) == -40.0  # Equal in both scales

        # Test with floating point values
        assert pytest.approx(fahrenheit_to_celsius(99.5), 0.001) == 37.5  # Body temperature
        assert pytest.approx(fahrenheit_to_celsius(0), 0.001) == -17.778  # 0 degrees Fahrenheit

        # Test with very large and very small values
        assert fahrenheit_to_celsius(1832) == 1000.0
        assert pytest.approx(fahrenheit_to_celsius(-459.67), 0.001) == -273.15  # Absolute zero

    def test_conversion_roundtrip(self):
        """Test that converting from C to F and back preserves the original value."""
        temperatures = [-50, -20, 0, 10, 20, 30, 50, 75, 100]

        for temp_c in temperatures:
            # Convert to Fahrenheit
            temp_f = celsius_to_fahrenheit(temp_c)
            # Convert back to Celsius
            temp_c_again = fahrenheit_to_celsius(temp_f)
            # Should get the original value (within floating point precision)
            assert pytest.approx(temp_c, 0.001) == temp_c_again

    def test_extreme_values(self):
        """Test temperature conversions with extreme values."""
        # Absolute zero
        abs_zero_c = -273.15
        abs_zero_f = -459.67
        assert pytest.approx(celsius_to_fahrenheit(abs_zero_c), 0.01) == abs_zero_f
        assert pytest.approx(fahrenheit_to_celsius(abs_zero_f), 0.01) == abs_zero_c

        # Very high temperatures
        assert celsius_to_fahrenheit(5500) == 9932.0  # Surface of the sun
        assert fahrenheit_to_celsius(9932) == 5500.0

        # Very low temperatures
        assert pytest.approx(celsius_to_fahrenheit(-270), 0.01) == -454.0
        assert pytest.approx(fahrenheit_to_celsius(-450), 0.01) == -267.778 # Corrected expected value


class TestCPUTemperatureEstimation:
    """Tests for CPU temperature estimation from liquid temperature."""

    def test_estimate_cpu_from_liquid_temp_mode_0(self):
        """Test CPU temperature estimation using mode 0 (scaled offset)."""
        # Test with low liquid temperature (< 30°C)
        liquid_temp = 25
        offset = 15
        expected = liquid_temp + offset  # 25 + 15 = 40
        assert estimate_cpu_from_liquid_temp(liquid_temp, offset, mode=0) == expected

        # Test with medium liquid temperature (30-40°C)
        liquid_temp = 35
        offset = 15
        expected = liquid_temp + (offset * 1.2)  # 35 + (15 * 1.2) = 35 + 18 = 53
        assert estimate_cpu_from_liquid_temp(liquid_temp, offset, mode=0) == expected

        # Test with high liquid temperature (> 40°C)
        liquid_temp = 45
        offset = 15
        scaling_factor = 1.4
        expected = liquid_temp + (offset * scaling_factor)  # 45 + (15 * 1.4) = 45 + 21 = 66
        assert estimate_cpu_from_liquid_temp(liquid_temp, offset, scaling_factor, mode=0) == expected

        # Test with custom scaling factor
        liquid_temp = 45
        offset = 15
        scaling_factor = 2.0
        expected = liquid_temp + (offset * scaling_factor)  # 45 + (15 * 2.0) = 45 + 30 = 75
        assert estimate_cpu_from_liquid_temp(liquid_temp, offset, scaling_factor, mode=0) == expected

    def test_estimate_cpu_from_liquid_temp_mode_1(self):
        """Test CPU temperature estimation using mode 1 (empirical formula)."""
        # Using the formula: (-727.5 + (30 * liquid_temp)) / 7.5

        # Test with low temperature
        liquid_temp = 25
        expected = 3.0 # (-727.5 + (30 * liquid_temp)) / 7.5  # (-727.5 + 750) / 7.5 = 22.5 / 7.5 = 3
        assert pytest.approx(estimate_cpu_from_liquid_temp(liquid_temp, mode=1), 0.001) == expected

        # Test with medium temperature
        liquid_temp = 35
        expected = 43.0 # (-727.5 + (30 * liquid_temp)) / 7.5  # (-727.5 + 1050) / 7.5 = 322.5 / 7.5 = 43
        assert pytest.approx(estimate_cpu_from_liquid_temp(liquid_temp, mode=1), 0.001) == expected

        # Test with high temperature
        liquid_temp = 45
        expected = 83.0 # (-727.5 + (30 * liquid_temp)) / 7.5  # (-727.5 + 1350) / 7.5 = 622.5 / 7.5 = 83
        assert pytest.approx(estimate_cpu_from_liquid_temp(liquid_temp, mode=1), 0.001) == expected

    def test_estimate_cpu_with_default_parameters(self):
        """Test CPU temperature estimation with default parameters."""
        # Default is mode=1
        liquid_temp = 30
        expected = 23.0 # (-727.5 + (30 * liquid_temp)) / 7.5 = (-727.5 + 900) / 7.5 = 172.5 / 7.5 = 23
        assert pytest.approx(estimate_cpu_from_liquid_temp(liquid_temp), 0.001) == expected

        # Verify that offset and scaling_factor don't affect mode 1
        assert (estimate_cpu_from_liquid_temp(liquid_temp) ==
                estimate_cpu_from_liquid_temp(liquid_temp, 20, 2.0))

    def test_extreme_values(self):
        """Test CPU estimation with extreme liquid temperature values."""
        # Very low temperature
        assert estimate_cpu_from_liquid_temp(0, mode=0) == 15  # Just offset
        # Mode 1 with very low temperature (might give unrealistic CPU temp)
        assert pytest.approx(estimate_cpu_from_liquid_temp(0, mode=1), 0.001) == -97.0

        # Very high temperature
        assert estimate_cpu_from_liquid_temp(100, mode=0) == 100 + (15 * 1.4)  # 121
        # Mode 1 with very high temperature
        assert pytest.approx(estimate_cpu_from_liquid_temp(100, mode=1), 0.001) == 303.0

        # Edge case: liquid temp = CPU temp in mode 0 with offset = 0
        assert estimate_cpu_from_liquid_temp(50, 0, 1.0, mode=0) == 50


class TestFanSpeedCalculation:
    """Tests for fan speed calculation functions."""

    def test_calculate_safe_fan_speed_default_range(self):
        """Test calculate_safe_fan_speed with default temperature range."""
        # Default range: min_temp=30, max_temp=75
        # Default speed range: min_speed=20, max_speed=100

        # At minimum temperature, should get minimum speed
        assert calculate_safe_fan_speed(30) == 20

        # At maximum temperature, should get maximum speed
        assert calculate_safe_fan_speed(75) == 100

        # At midpoint, should get midpoint speed
        # Midpoint temp = 30 + (75 - 30) / 2 = 52.5
        # Midpoint speed = 20 + (100 - 20) / 2 = 60
        assert calculate_safe_fan_speed(52.5) == 60

        # Test other points within the range
        # For temps in range 30-75, speed should scale linearly from 20-100
        # Temp 40 is (40-30)/(75-30) = 10/45 = 2/9 = 0.222... of the way
        # Expected speed = 20 + (100 - 20) * (10/45) = 20 + 80 * (2/9) = 20 + 160/9 = 20 + 17.77... = 37.77... -> rounded to 38
        assert calculate_safe_fan_speed(40) == 38
        # Temp 60 is (60-30)/(75-30) = 30/45 = 2/3 = 0.666... of the way
        # Expected speed = 20 + 80 * (2/3) = 20 + 160/3 = 20 + 53.33... = 73.33... -> rounded to 73
        assert calculate_safe_fan_speed(60) == 73

    def test_calculate_safe_fan_speed_custom_range(self):
        """Test calculate_safe_fan_speed with custom temperature and speed ranges."""
        # Define custom ranges
        min_temp = 40
        max_temp = 80
        min_speed = 30
        max_speed = 90

        # At minimum temperature, should get minimum speed
        assert calculate_safe_fan_speed(40, min_temp, max_temp, min_speed, max_speed) == 30

        # At maximum temperature, should get maximum speed
        assert calculate_safe_fan_speed(80, min_temp, max_temp, min_speed, max_speed) == 90

        # At midpoint, should get midpoint speed
        # Midpoint temp = 40 + (80 - 40) / 2 = 60
        # Midpoint speed = 30 + (90 - 30) / 2 = 60
        assert calculate_safe_fan_speed(60, min_temp, max_temp, min_speed, max_speed) == 60

        # Test inverted speed range (cooling down as temperature increases)
        # Midpoint temp = 60
        # Midpoint speed = 90 + (30 - 90) / 2 = 90 + (-60) / 2 = 90 - 30 = 60
        assert calculate_safe_fan_speed(60, min_temp, max_temp, 90, 30) == 60

    def test_calculate_safe_fan_speed_clamping(self):
        """Test that temperatures outside the range are properly clamped."""
        # Below minimum temperature, should get minimum speed
        assert calculate_safe_fan_speed(0) == 20
        assert calculate_safe_fan_speed(-10) == 20

        # Above maximum temperature, should get maximum speed
        assert calculate_safe_fan_speed(80) == 100
        assert calculate_safe_fan_speed(100) == 100

        # Test with custom range
        min_temp = 40
        max_temp = 80
        min_speed = 30
        max_speed = 90

        assert calculate_safe_fan_speed(30, min_temp, max_temp, min_speed, max_speed) == 30
        assert calculate_safe_fan_speed(90, min_temp, max_temp, min_speed, max_speed) == 90

    def test_calculate_safe_fan_speed_edge_cases(self):
        """Test calculate_safe_fan_speed with edge cases."""
        # When min_temp equals max_temp, should return max_speed to be safe
        assert calculate_safe_fan_speed(50, 50, 50, 20, 100) == 100

        # When min_speed equals max_speed, should always return that speed
        assert calculate_safe_fan_speed(40, 30, 75, 50, 50) == 50
        assert calculate_safe_fan_speed(60, 30, 75, 50, 50) == 50

        # Test with floating point temps
        # Expected: 20 + ((45.5-30)/(75-30)) * 80 = 20 + (15.5/45) * 80 = 20 + 0.3444 * 80 = 20 + 27.555... = 47.555... -> rounded to 48
        assert calculate_safe_fan_speed(45.5) == 48

    def test_calculate_safe_fan_speed(self):
        """Test safe fan speed calculation."""
        # Using default values for clarity in some tests
        min_temp_def, max_temp_def = 30, 75
        min_speed_def, max_speed_def = 20, 100

        assert calculate_safe_fan_speed(30, min_temp_def, max_temp_def, min_speed_def, max_speed_def) == 20
        assert calculate_safe_fan_speed(75, min_temp_def, max_temp_def, min_speed_def, max_speed_def) == 100
        # Midpoint: 52.5 -> speed 60
        assert calculate_safe_fan_speed(52.5, min_temp_def, max_temp_def, min_speed_def, max_speed_def) == 60
        # Below range
        assert calculate_safe_fan_speed(20, min_temp_def, max_temp_def, min_speed_def, max_speed_def) == 20
        # Above range
        assert calculate_safe_fan_speed(85, min_temp_def, max_temp_def, min_speed_def, max_speed_def) == 100

        # Edge cases
        assert calculate_safe_fan_speed(50, min_temp=50, max_temp=50, min_speed=20, max_speed=100) == 100
        assert calculate_safe_fan_speed(50, min_temp=30, max_temp=75, min_speed=60, max_speed=60) == 60

        # Inverted temperature range (should still work if logic handles it)
        # When temperature range is inverted (min_temp > max_temp), the function:
        # 1. Swaps min_temp and max_temp
        # 2. Swaps min_speed and max_speed to maintain the correct mapping
        # 3. Then performs the calculation
        
        # For inverted case:
        # - Original params: temp=60, min_temp=75, max_temp=30, min_speed=20, max_speed=100
        # - After swapping: temp=60, min_temp=30, max_temp=75, min_speed=100, max_speed=20
        # - Calculation: 
        #   normalized = (60 - 30) / (75 - 30) = 30 / 45 = 2/3
        #   speed = 100 + (2/3) * (20 - 100) = 100 - (2/3) * 80 = 100 - 53.33 = 46.67 -> rounded to 47
        assert calculate_safe_fan_speed(60, min_temp=75, max_temp=30, min_speed=20, max_speed=100) == 47

        # Test with standard (non-inverted) temperature range
        # Temp 60 is (60-30)/(75-30) = 30/45 = 2/3 of the way
        # Speed = 20 + (100-20) * (2/3) = 20 + 80 * (2/3) = 20 + 53.33 = 73.33 -> rounded to 73
        assert calculate_safe_fan_speed(60, min_temp=30, max_temp=75, min_speed=20, max_speed=100) == 73

        # Inverted speed range with normal temperature range
        # Temp 60 -> proportion 2/3 from min_temp
        # Speed = 100 + (20 - 100) * (2/3) = 100 - 53.33 = 46.67 -> rounded to 47
        assert calculate_safe_fan_speed(60, min_temp=30, max_temp=75, min_speed=100, max_speed=20) == 47

    def test_gpu_temp_to_fan_speed(self):
        """Test gpu_temp_to_fan_speed with various temperatures."""
        # GPU fan speed formula: max(0, min(100, round(((5 * temp) - 100) * 0.5)))

        # Test extreme low temperature (should clamp to 0)
        # For temp=0: ((5 * 0) - 100) * 0.5 = -50 -> clamped to 0
        assert gpu_temp_to_fan_speed(0) == 0

        # Test low temperature (below the 0% threshold)
        # For temp=30: ((5 * 30) - 100) * 0.5 = (150 - 100) * 0.5 = 25
        assert gpu_temp_to_fan_speed(30) == 25

        # Test mid-range temperature
        # For temp=50: ((5 * 50) - 100) * 0.5 = (250 - 100) * 0.5 = 75
        assert gpu_temp_to_fan_speed(50) == 75

        # Test high temperature (should clamp to 100)
        # For temp=70: ((5 * 70) - 100) * 0.5 = (350 - 100) * 0.5 = 125 -> clamped to 100
        assert gpu_temp_to_fan_speed(70) == 100

        # Test with temperature modifier (assuming modifier adds to temp before calculation)
        # For temp=50, modifier=10 (assuming modifier is an additive offset for simplicity, adjust if it's multiplicative)
        # Effective temp = 50 + 10 = 60
        # Speed = ((5 * 60) - 100) * 0.5 = (300 - 100) * 0.5 = 100
        # Let's assume the original intent was multiplicative: temp * (1 + modifier)
        # For temp=50, modifier=0.1: Effective temp = 50 * 1.1 = 55
        # Speed = ((5 * 55) - 100) * 0.5 = (275 - 100) * 0.5 = 175 * 0.5 = 87.5 -> rounded to 88
        assert gpu_temp_to_fan_speed(50, 0.1) == 88 # Assuming multiplicative modifier

    def test_cpu_temp_to_fan_speed(self):
        """Test cpu_temp_to_fan_speed with various temperatures."""
        # CPU fan speed formula: max(0, min(100, round((6 * temp) - 200)))

        # Test extreme low temperature (should clamp to 0)
        assert cpu_temp_to_fan_speed(30) == 0  # (6 * 30) - 200 = 180 - 200 = -20 -> 0

        # Test at the 0% threshold
        # At temp=33.33..., speed should be just below 0: (6 * 33.33) - 200 = 199.98 - 200 = -0.02 -> round(0) -> 0
        # At temp=33.5, speed should be just above 0: (6 * 33.5) - 200 = 201 - 200 = 1 -> round(1) -> 1
        assert cpu_temp_to_fan_speed(33.33) == 0
        assert cpu_temp_to_fan_speed(33.5) == 1 # Crossing point

        # Test at the crossing point (0% to positive %)
        assert cpu_temp_to_fan_speed(34) == 4  # (6 * 34) - 200 = 204 - 200 = 4

        # Test mid-range temperature
        # At temp=50, speed should be 100: (6 * 50) - 200 = 300 - 200 = 100
        assert cpu_temp_to_fan_speed(50) == 100

        # Test high temperature (approaching 100%)
        # At temp=49, speed should be < 100: (6 * 49) - 200 = 294 - 200 = 94
        assert cpu_temp_to_fan_speed(49) == 94
        assert cpu_temp_to_fan_speed(50) == 100 # Hits 100 exactly at 50

        # Test extremely high temperature (should clamp to 100)
        assert cpu_temp_to_fan_speed(60) == 100  # (6 * 60) - 200 = 360 - 200 = 160 -> clamped to 100
        assert cpu_temp_to_fan_speed(100) == 100


# --- Refactored TestTemperatureUtils using pytest style ---

class TestTemperatureUtilsPytest:
    """Test cases for temperature utilities using pytest assertions."""

    def test_celsius_to_fahrenheit(self):
        """Test Celsius to Fahrenheit conversion."""
        assert celsius_to_fahrenheit(0) == 32
        assert celsius_to_fahrenheit(100) == 212
        assert celsius_to_fahrenheit(-40) == -40
        assert pytest.approx(celsius_to_fahrenheit(50)) == 122
        assert pytest.approx(celsius_to_fahrenheit(85)) == 185

    def test_fahrenheit_to_celsius(self):
        """Test Fahrenheit to Celsius conversion."""
        assert fahrenheit_to_celsius(32) == 0
        assert fahrenheit_to_celsius(212) == 100
        assert fahrenheit_to_celsius(-40) == -40
        assert pytest.approx(fahrenheit_to_celsius(122)) == 50
        assert pytest.approx(fahrenheit_to_celsius(185)) == 85

    def test_normalize_temperature(self):
        """Test temperature normalization."""
        assert normalize_temperature(50) == 50
        assert normalize_temperature(-10) == 0
        assert normalize_temperature(150) == 100
        assert normalize_temperature(60, min_temp=20, max_temp=80) == 60
        assert normalize_temperature(10, min_temp=20, max_temp=80) == 20
        assert normalize_temperature(90, min_temp=20, max_temp=80) == 80

    def test_average_temperatures(self):
        """Test temperature averaging."""
        assert average_temperatures([10, 20, 30, 40, 50]) == 30
        with pytest.raises(ValueError):
            average_temperatures([])
        temps = [20, 21, 22, 23, 100]
        assert pytest.approx(average_temperatures(temps)) == 37.2
        assert pytest.approx(
            average_temperatures(temps, discard_outliers=True)
        ) == 21.5
        assert average_temperatures([42, 42, 42]) == 42

    def test_calculate_temperature_trend(self):
        """Test temperature trend calculation."""
        slope, trend = calculate_temperature_trend([20, 22, 25, 28, 32])
        assert slope > 0
        assert trend == "rising"

        slope, trend = calculate_temperature_trend([50, 48, 45, 43, 40])
        assert slope < 0
        assert trend == "falling"

        slope, trend = calculate_temperature_trend([25, 25.1, 24.9, 25.2, 25])
        # Slope might be very close to zero, check trend directly
        assert trend == "stable"

        slope, trend = calculate_temperature_trend([42])
        assert slope == 0.0
        assert trend == "stable"

    def test_create_temperature_window(self):
        """Test temperature window creation."""
        window = create_temperature_window()
        assert window.get_capacity() == 10
        assert window.get_average() == 0

        window = create_temperature_window(size=5, initial_value=20)
        assert window.get_capacity() == 5
        assert window.get_average() == 20

        window = create_temperature_window(size=3, initial_value=0)
        window.add(30)
        assert window.get_average() == 10  # (0 + 0 + 30) / 3
        window.add(60)
        assert window.get_average() == 30  # (0 + 30 + 60) / 3
        window.add(90)
        assert window.get_average() == 60  # (30 + 60 + 90) / 3

    def test_temperature_within_range(self):
        """Test temperature range checking."""
        assert temperature_within_range(50, 50)
        assert temperature_within_range(51, 50)
        assert temperature_within_range(48, 50)
        assert not temperature_within_range(47, 50)
        assert not temperature_within_range(53, 50)
        assert temperature_within_range(45, 50, tolerance=5)
        assert temperature_within_range(55, 50, tolerance=5)
        assert not temperature_within_range(44, 50, tolerance=5)
        assert not temperature_within_range(56, 50, tolerance=5)

    def test_classify_temperature(self):
        """Test temperature classification."""
        assert classify_temperature(25) == "cool"
        assert classify_temperature(35) == "normal"
        assert classify_temperature(50) == "warm"
        assert classify_temperature(70) == "hot"
        assert classify_temperature(90) == "critical"

        custom_ranges = [
            (0, 20, "freezing"),
            (20, 40, "cold"),
            (40, 60, "moderate"),
            (60, 80, "hot"),
            (80, 100, "extreme")
        ]
        assert classify_temperature(15, custom_ranges) == "freezing"
        assert classify_temperature(30, custom_ranges) == "cold"
        assert classify_temperature(50, custom_ranges) == "moderate"
        assert classify_temperature(70, custom_ranges) == "hot"
        assert classify_temperature(90, custom_ranges) == "extreme"

    def test_estimate_cpu_from_liquid_temp(self):
        """Test CPU temperature estimation from liquid temp."""
        # Mode 0
        assert estimate_cpu_from_liquid_temp(25, offset=15, mode=0) == 40
        assert estimate_cpu_from_liquid_temp(35, offset=15, mode=0) == 53
        assert estimate_cpu_from_liquid_temp(45, offset=15, scaling_factor=1.4, mode=0) == 66

        # Mode 1
        # Expected values recalculated based on formula: (-727.5 + (30 * liquid_temp)) / 7.5
        assert pytest.approx(estimate_cpu_from_liquid_temp(30, mode=1)) == 23.0
        assert pytest.approx(estimate_cpu_from_liquid_temp(40, mode=1)) == 63.0 # Corrected expected value

    def test_calculate_safe_fan_speed(self):
        """Test safe fan speed calculation."""
        # Using default values for clarity in some tests
        min_temp_def, max_temp_def = 30, 75
        min_speed_def, max_speed_def = 20, 100

        assert calculate_safe_fan_speed(30, min_temp_def, max_temp_def, min_speed_def, max_speed_def) == 20
        assert calculate_safe_fan_speed(75, min_temp_def, max_temp_def, min_speed_def, max_speed_def) == 100
        # Midpoint: 52.5 -> speed 60
        assert calculate_safe_fan_speed(52.5, min_temp_def, max_temp_def, min_speed_def, max_speed_def) == 60
        # Below range
        assert calculate_safe_fan_speed(20, min_temp_def, max_temp_def, min_speed_def, max_speed_def) == 20
        # Above range
        assert calculate_safe_fan_speed(85, min_temp_def, max_temp_def, min_speed_def, max_speed_def) == 100

        # Edge cases
        assert calculate_safe_fan_speed(50, min_temp=50, max_temp=50, min_speed=20, max_speed=100) == 100
        assert calculate_safe_fan_speed(50, min_temp=30, max_temp=75, min_speed=60, max_speed=60) == 60

        # Inverted temperature range (should still work if logic handles it)
        # When temperature range is inverted (min_temp > max_temp), the function:
        # 1. Swaps min_temp and max_temp
        # 2. Swaps min_speed and max_speed to maintain the correct mapping
        # 3. Then performs the calculation
        
        # For inverted case:
        # - Original params: temp=60, min_temp=75, max_temp=30, min_speed=20, max_speed=100
        # - After swapping: temp=60, min_temp=30, max_temp=75, min_speed=100, max_speed=20
        # - Calculation: 
        #   normalized = (60 - 30) / (75 - 30) = 30 / 45 = 2/3
        #   speed = 100 + (2/3) * (20 - 100) = 100 - (2/3) * 80 = 100 - 53.33 = 46.67 -> rounded to 47
        assert calculate_safe_fan_speed(60, min_temp=75, max_temp=30, min_speed=20, max_speed=100) == 47

        # Test with standard (non-inverted) temperature range
        # Temp 60 is (60-30)/(75-30) = 30/45 = 2/3 of the way
        # Speed = 20 + (100-20) * (2/3) = 20 + 80 * (2/3) = 20 + 53.33 = 73.33 -> rounded to 73
        assert calculate_safe_fan_speed(60, min_temp=30, max_temp=75, min_speed=20, max_speed=100) == 73

        # Inverted speed range with normal temperature range
        # Temp 60 -> proportion 2/3 from min_temp
        # Speed = 100 + (20 - 100) * (2/3) = 100 - 53.33 = 46.67 -> rounded to 47
        assert calculate_safe_fan_speed(60, min_temp=30, max_temp=75, min_speed=100, max_speed=20) == 47

    def test_gpu_temp_to_fan_speed(self):
        """Test GPU temperature to fan speed conversion."""
        # Formula: max(0, min(100, round(((5 * temp) - 100) * 0.5)))
        # Original test had temp=30 -> 25, but clamped to 0. This seems wrong based on formula.
        # Let's use the calculated values:
        assert gpu_temp_to_fan_speed(30) == 25 # ((5 * 30) - 100) / 2 = 25
        assert gpu_temp_to_fan_speed(50) == 75 # ((5 * 50) - 100) / 2 = 75
        assert gpu_temp_to_fan_speed(70) == 100 # ((5 * 70) - 100) / 2 = 125 -> clamped to 100
        # Test with modifier (assuming multiplicative: temp * (1 + modifier))
        # temp=40, modifier=1 -> effective temp = 40 * (1+1) = 80
        # speed = ((5 * 80) - 100) / 2 = (400 - 100) / 2 = 150 -> clamped to 100
        assert gpu_temp_to_fan_speed(40, modifier=1) == 100

    def test_cpu_temp_to_fan_speed(self):
        """Test CPU temperature to fan speed conversion."""
        # Formula: max(0, min(100, round((6 * temp) - 200)))
        assert cpu_temp_to_fan_speed(30) == 0   # (6 * 30) - 200 = -20 -> 0
        assert cpu_temp_to_fan_speed(42) == 52  # (6 * 42) - 200 = 252 - 200 = 52
        assert cpu_temp_to_fan_speed(50) == 100 # (6 * 50) - 200 = 100
        assert cpu_temp_to_fan_speed(60) == 100 # (6 * 60) - 200 = 160 -> 100


class TestFanCurves:
    """Tests for fan curve behavior under different temperature scenarios."""

    def test_cpu_fan_curve_progression(self):
        """Test that the CPU fan curve increases appropriately with temperature."""
        previous_speed = -1 # Initialize to allow 0 speed

        for temp in range(25, 71, 5):
            current_speed = cpu_temp_to_fan_speed(temp)
            assert current_speed >= previous_speed
            assert 0 <= current_speed <= 100
            previous_speed = current_speed

    def test_gpu_fan_curve_progression(self):
        """Test that the GPU fan curve increases appropriately with temperature."""
        previous_speed = -1 # Initialize to allow 0 speed

        for temp in range(25, 71, 5):
            current_speed = gpu_temp_to_fan_speed(temp)
            assert current_speed >= previous_speed
            assert 0 <= current_speed <= 100
            previous_speed = current_speed

    def test_linear_fan_curve_progression(self):
        """Test that the linear fan curve (calculate_safe_fan_speed) increases appropriately."""
        previous_speed = -1 # Initialize to allow 0 speed

        for temp in range(25, 71, 5):
            # Using a specific range for testing linearity
            current_speed = calculate_safe_fan_speed(temp, min_temp=30, max_temp=60, min_speed=10, max_speed=90)
            assert current_speed >= previous_speed
            assert 0 <= current_speed <= 100 # Check general bounds
            # Check specific bounds for this curve
            assert 10 <= current_speed <= 90 or temp < 30 or temp > 60
            previous_speed = current_speed


class TestAcrossTemperatureRanges:
    """Tests for functions across different temperature ranges relevant to computing."""

    # Adjusted expected ranges based on function calculations
    @pytest.mark.parametrize("temp,expected_cpu_range,expected_gpu_range", [
        (20, (0, 0),   (0, 0)),      # Below idle -> 0 speed for both
        (35, (10, 10), (38, 38)),    # Idle temperature -> CPU: 10, GPU: 38
        (50, (100, 100),(75, 75)),   # Light/Mid load -> CPU: 100, GPU: 75
        (65, (100, 100),(100, 100)), # Medium/Heavy load -> CPU: 100, GPU: 100
        (80, (100, 100),(100, 100)), # Heavy load -> Both 100
        (95, (100, 100),(100, 100)), # Critical temperature -> Both 100
    ])
    def test_temperature_responses(self, temp, expected_cpu_range, expected_gpu_range):
        """Test that different functions respond appropriately to various temperature ranges."""
        # CPU fan response
        cpu_speed = cpu_temp_to_fan_speed(temp)
        assert expected_cpu_range[0] <= cpu_speed <= expected_cpu_range[1]

        # GPU fan response
        gpu_speed = gpu_temp_to_fan_speed(temp)
        assert expected_gpu_range[0] <= gpu_speed <= expected_gpu_range[1]

        # Linear response (for comparison - ensure it stays within bounds)
        linear_speed = calculate_safe_fan_speed(temp, min_temp=30, max_temp=80)
        assert 0 <= linear_speed <= 100

    def test_temperature_estimation_consistency(self):
        """Test that CPU temperature estimation is consistent with fan speed calculations."""
        previous_fan_speed = -1
        for liquid_temp in range(30, 61, 5):
            # Using mode 1 as default
            estimated_cpu = estimate_cpu_from_liquid_temp(liquid_temp, mode=1)

            # Calculate fan speed based on estimated CPU temperature
            fan_speed = cpu_temp_to_fan_speed(estimated_cpu)

            # As liquid temperature increases, estimated CPU temp should increase,
            # and thus fan speed should generally increase or stay the same (due to clamping).
            assert 0 <= fan_speed <= 100
            assert fan_speed >= previous_fan_speed # Check non-decreasing trend

            # A more specific check based on mode 1 estimation:
            # liquid=30 -> est_cpu=23 -> speed=0
            # liquid=35 -> est_cpu=43 -> speed=58
            # liquid=40 -> est_cpu=63 -> speed=100
            if liquid_temp >= 40:
                # Based on mode 1, CPU temp estimate exceeds 50C quickly, leading to 100% fan speed
                assert fan_speed == 100
            elif liquid_temp == 35:
                 assert fan_speed == 58 # (6*43)-200 = 258-200 = 58
            elif liquid_temp == 30:
                 assert fan_speed == 0 # (6*23)-200 = 138-200 = -62 -> 0

            previous_fan_speed = fan_speed
