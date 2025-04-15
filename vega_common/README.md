# Vega Common Library

A shared utility library for the Vega project that provides common functionality across different components (rootspace, userspace, gateway, and client).

## Overview

The `vega_common` library centralizes utilities used throughout the Vega ecosystem, ensuring consistent behavior, improving code maintainability, and reducing duplication.

## Features

- **File Manipulation**: Robust file handling with proper error management
- **List Processing**: Utilities for working with lists, arrays, and sliding windows
- **Subprocess Execution**: Safe and flexible command execution utilities
- **DateTime Operations**: Consistent date and time formatting and manipulation
- **Color Utilities**: Color format conversion (RGB, HSV, HEX) and manipulation functions
- **Temperature Utilities**: Temperature conversion, estimation, and fan speed calculation

## Library Structure

```plaintext
vega_common/
├── __init__.py        # Main package file with shortcuts to common functions
├── setup.py           # Installation configuration
└── utils/             # Utility modules
    ├── __init__.py
    ├── color_utils.py        # Color manipulation and conversion functions
    ├── datetime_utils.py     # Date and time handling functions
    ├── files_manipulation.py # File I/O with enhanced error handling
    ├── list_process.py       # List manipulation utilities
    ├── sub_process.py        # Shell command execution utilities
    └── temperature_utils.py  # Temperature conversion and calculation functions
```

## Installation

Install the library in development mode:

```bash
cd /path/to/vega
pip install -e ./vega_common
```

## Usage Examples

### Color Utilities

```python
from vega_common.utils.color_utils import rgb_to_hsv, hsv_to_rgb, hex_to_rgb, rgb_to_hex, shift_hue, adjust_brightness

# Convert between color formats
rgb_color = [255, 0, 0]  # Red in RGB
hsv_color = rgb_to_hsv(rgb_color)  # Convert to HSV
print(f"Red in HSV: {hsv_color}")  # [0, 100, 100]

# Convert from HSV back to RGB
rgb_color = hsv_to_rgb(hsv_color)
print(f"Back to RGB: {rgb_color}")  # [255, 0, 0]

# Convert RGB to hex color string
hex_color = rgb_to_hex(255, 0, 0)
print(f"Red in hex: {hex_color}")  # #ff0000

# Convert hex color to RGB
rgb_from_hex = hex_to_rgb("#ff0000")
print(f"Hex to RGB: {rgb_from_hex}")  # [255, 0, 0]

# Color manipulation functions
shifted_hsv = shift_hue(hsv_color.copy(), 120)  # Shift hue by 120 degrees (red -> green)
print(f"Shifted hue: {shifted_hsv}")  # [120, 100, 100]

brightened_hsv = adjust_brightness(hsv_color.copy(), 10)  # Increase brightness
print(f"Brightened color: {brightened_hsv}")  # [0, 100, 110] (capped at 100)
```

### Temperature Utilities

```python
from vega_common.utils.temperature_utils import celsius_to_fahrenheit, calculate_safe_fan_speed, estimate_cpu_from_liquid_temp

# Convert temperature units
temp_c = 30
temp_f = celsius_to_fahrenheit(temp_c)
print(f"{temp_c}°C is {temp_f}°F")  # 30°C is 86.0°F

# Calculate fan speed based on temperature
cpu_temp = 65
fan_speed = calculate_safe_fan_speed(cpu_temp, min_temp=40, max_temp=80, min_speed=30, max_speed=100)
print(f"CPU at {cpu_temp}°C needs {fan_speed}% fan speed")  # CPU at 65°C needs 73% fan speed

# Estimate CPU temperature from liquid cooling temperature
liquid_temp = 35
estimated_cpu = estimate_cpu_from_liquid_temp(liquid_temp)
print(f"Liquid at {liquid_temp}°C suggests CPU around {estimated_cpu}°C")  # Estimation based on liquid temp
```

## Testing

The library includes a comprehensive test suite using pytest to ensure all functionality works correctly across different contexts.

### Test Directory Structure

```plaintext
tests/
├── conftest.py                          # Global pytest configuration
└── vega_common/
    └── utils/
        ├── test_color_utils.py          # Tests for color utilities
        ├── test_datetime_utils.py       # Tests for datetime utilities
        ├── test_files_manipulation.py   # Tests for file operations
        ├── test_list_process.py         # Tests for list manipulation
        ├── test_sub_process.py          # Tests for subprocess operations
        └── test_temperature_utils.py    # Tests for temperature utilities
```

### Running Tests

There are several ways to run the tests depending on your requirements:

#### Running All Tests

```bash
# From the vega_common directory
pytest

# Or more explicitly
pytest tests/
```

#### Running Specific Test Modules

```bash
# Run tests for a specific utility
pytest tests/vega_common/utils/test_datetime_utils.py

# Run tests for multiple modules
pytest tests/vega_common/utils/test_datetime_utils.py tests/vega_common/utils/test_list_process.py
```

#### Running Tests by Name Pattern

```bash
# Run all tests with "format" in their name
pytest -k "format"

# Run all tests in a class
pytest -k "TestGetCurrentTime"
```

#### Verbose Output

```bash
# Add -v for verbose output
pytest -v tests/

# Add -vv for even more verbose output
pytest -vv tests/
```

### Test Coverage Analysis

The test suite includes code coverage analysis using pytest-cov:

```bash
# Generate coverage report in terminal
pytest --cov=vega_common tests/

# Generate detailed coverage report
pytest --cov=vega_common --cov-report=term-missing tests/

# Generate HTML coverage report
pytest --cov=vega_common --cov-report=html tests/
# This creates a htmlcov/ directory with an interactive HTML report
```

### Continuous Integration Testing

You can integrate these tests into a CI/CD pipeline by running:

```bash
# Run tests and generate JUnit XML report for CI systems
pytest --junitxml=test-results.xml tests/

# Run tests with coverage and export for CI systems
pytest --cov=vega_common --cov-report=xml tests/
```

### Test Dependencies

The test suite requires the following packages:

- pytest
- pytest-cov
- freezegun (for time-related tests)

These can be installed via:

```bash
pip install pytest pytest-cov freezegun
```

## Best Practices for Testing

When adding new functionality to the library:

1. **Write Tests First**: Follow Test-Driven Development (TDD) principles
2. **Test Edge Cases**: Include tests for boundary conditions and unexpected inputs
3. **Maintain Independence**: Ensure tests are independent and don't affect each other
4. **Use Fixtures**: Use pytest fixtures for setup and teardown
5. **Mock External Dependencies**: Use monkeypatch or unittest.mock for external dependencies

## Documentation

Each module, class, and function in the library includes comprehensive docstrings that explain:

- Purpose and functionality
- Input parameters and return values
- Exceptions that may be raised
- Usage examples

Run `pydoc` to view the documentation:

```bash
pydoc vega_common.utils.datetime_utils
```
