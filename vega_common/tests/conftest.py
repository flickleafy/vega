"""
Pytest configuration for vega_common library tests.

This file contains shared fixtures and configuration for all tests.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path to ensure imports work correctly
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))