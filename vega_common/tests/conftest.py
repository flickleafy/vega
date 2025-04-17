"""
Pytest configuration for the vega_common test suite.

This module contains fixtures and configuration settings for the test suite.
"""
import os
import sys
import pytest

# Add the project root to the path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def pytest_addoption(parser):
    """Add custom command line options to pytest."""
    parser.addoption(
        "--runperf",
        action="store_true",
        default=False,
        help="Run performance tests that are skipped by default"
    )


@pytest.fixture
def run_performance_tests(request):
    """
    Fixture to determine if performance tests should run.
    
    Returns:
        bool: True if performance tests should run, False otherwise.
    """
    return request.config.getoption("--runperf")


@pytest.fixture
def sample_rgb_colors():
    """
    Fixture providing common RGB color values for tests.
    
    Returns:
        dict: A dictionary of common RGB colors.
    """
    return {
        'red': [255, 0, 0],
        'green': [0, 255, 0],
        'blue': [0, 0, 255],
        'black': [0, 0, 0],
        'white': [255, 255, 255],
        'gray': [128, 128, 128],
    }


@pytest.fixture
def sample_hsv_colors():
    """
    Fixture providing common HSV color values for tests.
    
    Returns:
        dict: A dictionary of common HSV colors.
    """
    return {
        'red': [0, 100, 100],
        'green': [120, 100, 100],
        'blue': [240, 100, 100],
        'black': [0, 0, 0],
        'white': [0, 0, 100],
        'gray': [0, 0, 50],
    }


@pytest.fixture
def sample_hex_colors():
    """
    Fixture providing common HEX color values for tests.
    
    Returns:
        dict: A dictionary of common HEX colors.
    """
    return {
        'red': 'ff0000',
        'green': '00ff00',
        'blue': '0000ff',
        'black': '000000',
        'white': 'ffffff',
        'gray': '808080',
    }