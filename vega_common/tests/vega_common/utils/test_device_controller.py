"""
Unit tests for device_controller.py module.

This test file provides complete coverage for the DeviceController abstract base class.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any

from vega_common.utils.device_controller import DeviceController


class ConcreteDeviceController(DeviceController):
    """
    Concrete implementation of DeviceController for testing purposes.
    
    This class implements the abstract methods required by DeviceController.
    """
    
    def __init__(self, device_id: str, device_type: str, device_name: str = None):
        """Initialize the concrete controller with mock settings."""
        super().__init__(device_id, device_type, device_name)
        self.mock_settings = {
            "setting1": 50,
            "setting2": "value"
        }
    
    def apply_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Apply the specified settings.
        
        Args:
            settings (Dict[str, Any]): Dictionary of settings to apply.
            
        Returns:
            bool: Always returns True for testing.
        """
        self.mock_settings.update(settings)
        return True
    
    def get_available_settings(self) -> Dict[str, Any]:
        """
        Get available settings and their current values.
        
        Returns:
            Dict[str, Any]: Dictionary of available settings.
        """
        return {
            "setting1": {
                "current": self.mock_settings["setting1"],
                "min": 0,
                "max": 100
            },
            "setting2": {
                "current": self.mock_settings["setting2"],
                "options": ["value", "other_value"]
            }
        }


class TestDeviceController:
    """Tests for the DeviceController class."""
    
    def test_initialization(self):
        """Test the initialization of a DeviceController."""
        # Test with required parameters only
        controller = ConcreteDeviceController("device-1", "test-type")
        assert controller.device_id == "device-1"
        assert controller.device_type == "test-type"
        assert controller.device_name is None
        
        # Test with device_name parameter
        controller = ConcreteDeviceController("device-2", "test-type", "Device 2")
        assert controller.device_id == "device-2"
        assert controller.device_type == "test-type"
        assert controller.device_name == "Device 2"
    
    def test_apply_settings(self):
        """Test the apply_settings method implementation."""
        controller = ConcreteDeviceController("device-1", "test-type")
        
        # Initial settings
        assert controller.mock_settings["setting1"] == 50
        assert controller.mock_settings["setting2"] == "value"
        
        # Apply new settings
        result = controller.apply_settings({"setting1": 75, "setting3": "new-value"})
        
        # Verify settings were applied and result is True
        assert result is True
        assert controller.mock_settings["setting1"] == 75
        assert controller.mock_settings["setting2"] == "value"
        assert controller.mock_settings["setting3"] == "new-value"
    
    def test_get_available_settings(self):
        """Test the get_available_settings method implementation."""
        controller = ConcreteDeviceController("device-1", "test-type")
        
        # Get settings
        settings = controller.get_available_settings()
        
        # Verify returned settings format and values
        assert "setting1" in settings
        assert "setting2" in settings
        assert settings["setting1"]["current"] == 50
        assert settings["setting1"]["min"] == 0
        assert settings["setting1"]["max"] == 100
        assert settings["setting2"]["current"] == "value"
        assert "options" in settings["setting2"]
        assert "value" in settings["setting2"]["options"]