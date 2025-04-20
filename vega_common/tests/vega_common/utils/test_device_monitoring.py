"""
Unit tests for the device_monitoring module.

Tests the functionality of the device monitoring framework to ensure
it behaves as expected across different contexts.
"""

import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from vega_common.utils.device_controller import DeviceController
from vega_common.utils.device_manager import DeviceManager
from vega_common.utils.device_status import DeviceStatus
from vega_common.utils.device_monitor import DeviceMonitor


class TestDeviceStatus:
    """Tests for the DeviceStatus class."""

    def test_initialization(self):
        """Test DeviceStatus initialization."""
        status = DeviceStatus("test-device-1", "test-type")

        assert status.device_id == "test-device-1"
        assert status.device_type == "test-type"
        assert status.status_properties == {}
        assert isinstance(status.last_update, datetime)

    def test_property_updates(self):
        """Test updating and getting properties."""
        status = DeviceStatus("test-device-1", "test-type")

        # Update properties
        status.update_property("temperature", 45.5)
        status.update_property("fan_speed", 60)
        status.update_property("status", "running")

        # Check property values
        assert status.get_property("temperature") == 45.5
        assert status.get_property("fan_speed") == 60
        assert status.get_property("status") == "running"

        # Check default value for non-existing property
        assert status.get_property("non_existent") is None
        assert status.get_property("non_existent", "default") == "default"

    def test_tracking_properties(self):
        """Test tracking property history."""
        status = DeviceStatus("test-device-1", "test-type")

        # Register a tracked property
        status.register_tracked_property("temperature", 0.0)

        # Update the property multiple times
        status.update_property("temperature", 30.0)
        status.update_property("temperature", 35.0)
        status.update_property("temperature", 40.0)

        # Check history values
        history = status.get_property_history("temperature")
        assert len(history) == 10
        # With a window size of 10 and 3 updates, we expect 7 default values (0.0) followed by 3 updates
        expected_history = [0.0] * 7 + [30.0, 35.0, 40.0]
        assert history == expected_history

        # Check average
        assert (
            status.get_property_average("temperature") == 10.5
        )  # (7*0.0 + 30.0 + 35.0 + 40.0) / 10 = 10.5

        # Check non-tracked property
        assert status.get_property_history("non_tracked") == []
        assert status.get_property_average("non_tracked") == 0.0

    def test_to_dict(self):
        """Test converting status to dictionary."""
        status = DeviceStatus("test-device-1", "test-type")
        status.update_property("temperature", 45.5)
        status.update_property("fan_speed", 60)

        # Register and track a property - use an empty sliding window with no default values
        status.register_tracked_property("temperature", None)
        status.update_property("temperature", 45.5)
        status.update_property("temperature", 50.5)

        # Convert to dict
        result = status.to_dict()

        assert result["device_id"] == "test-device-1"
        assert result["device_type"] == "test-type"
        assert result["temperature"] == 50.5
        assert result["fan_speed"] == 60
        assert "last_update" in result
        assert result["temperature_avg"] == 48.0  # (45.5 + 50.5) / 2


class MockDeviceMonitor(DeviceMonitor):
    """Mock implementation of DeviceMonitor for testing."""

    def __init__(self, device_id, device_type, monitoring_interval=0.1):
        # Explicitly pass 0.1 as the monitoring_interval to the parent class
        super().__init__(
            device_id=device_id,
            device_type=device_type,
            monitoring_interval=monitoring_interval,  # Pass this through to parent
            tracked_properties=["temperature", "load"],
        )
        self.update_count = 0
        self.mock_temperatures = [30, 32, 35, 38, 40]
        self.mock_loads = [20, 30, 40, 50, 60]

    def update_status(self):
        """Mock implementation that updates with fake data."""
        index = min(self.update_count, len(self.mock_temperatures) - 1)
        self.status.update_property("temperature", self.mock_temperatures[index])
        self.status.update_property("load", self.mock_loads[index])
        self.status.update_property("last_updated", datetime.now().isoformat())
        self.update_count += 1


class MockDeviceController(DeviceController):
    """Mock implementation of DeviceController for testing."""

    def __init__(self, device_id, device_type):
        super().__init__(device_id, device_type)
        self.current_settings = {"fan_speed": 50, "power_limit": 100}

    def apply_settings(self, settings):
        """Mock implementation that applies settings."""
        self.current_settings.update(settings)
        return True

    def get_available_settings(self):
        """Mock implementation that returns available settings."""
        return {
            "fan_speed": {"current": self.current_settings["fan_speed"], "min": 0, "max": 100},
            "power_limit": {"current": self.current_settings["power_limit"], "min": 50, "max": 150},
        }


class TestDeviceMonitor:
    """Tests for the DeviceMonitor class."""

    def test_initialization(self):
        """Test DeviceMonitor initialization."""
        monitor = MockDeviceMonitor("test-device-1", "test-type")

        assert monitor.device_id == "test-device-1"
        assert monitor.device_type == "test-type"
        assert (
            monitor.monitoring_interval == 0.1
        )  # Updated to match the expected value in MockDeviceMonitor
        assert not monitor.is_monitoring
        assert monitor.monitor_thread is None

    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        monitor = MockDeviceMonitor(
            "test-device-1", "test-type", monitoring_interval=0.05
        )  # Use even shorter interval

        # Start monitoring
        monitor.start_monitoring()
        assert monitor.is_monitoring
        assert monitor.monitor_thread is not None
        assert monitor.monitor_thread.is_alive()

        # Let it run for a bit to collect some data
        time.sleep(0.5)  # Increased sleep time to ensure multiple updates with shorter interval

        # Stop monitoring
        monitor.stop_monitoring()
        assert not monitor.is_monitoring
        assert not monitor.monitor_thread.is_alive()

        # Check that status was updated
        status_dict = monitor.get_status_dict()
        assert "temperature" in status_dict
        assert "load" in status_dict
        assert monitor.update_count >= 2

    def test_get_status_dict(self):
        """Test getting status as dictionary."""
        monitor = MockDeviceMonitor("test-device-1", "test-type")

        # Update status manually
        monitor.update_status()

        # Get status dict
        status_dict = monitor.get_status_dict()

        assert status_dict["device_id"] == "test-device-1"
        assert status_dict["device_type"] == "test-type"
        assert status_dict["temperature"] == 30
        assert status_dict["load"] == 20


class TestDeviceController:
    """Tests for the DeviceController class."""

    def test_initialization(self):
        """Test DeviceController initialization."""
        controller = MockDeviceController("test-device-1", "test-type")

        assert controller.device_id == "test-device-1"
        assert controller.device_type == "test-type"

    def test_apply_settings(self):
        """Test applying settings."""
        controller = MockDeviceController("test-device-1", "test-type")

        # Apply new settings
        result = controller.apply_settings({"fan_speed": 75, "power_limit": 120})

        assert result is True
        assert controller.current_settings["fan_speed"] == 75
        assert controller.current_settings["power_limit"] == 120

    def test_get_available_settings(self):
        """Test getting available settings."""
        controller = MockDeviceController("test-device-1", "test-type")

        settings = controller.get_available_settings()

        assert "fan_speed" in settings
        assert "power_limit" in settings
        assert settings["fan_speed"]["current"] == 50
        assert settings["fan_speed"]["min"] == 0
        assert settings["fan_speed"]["max"] == 100


class TestDeviceManager:
    """Tests for the DeviceManager class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.manager = DeviceManager()

        # Create some test monitors and controllers
        self.gpu_monitor = MockDeviceMonitor("gpu-1", "gpu")
        self.cpu_monitor = MockDeviceMonitor("cpu-1", "cpu")
        self.gpu_controller = MockDeviceController("gpu-1", "gpu")
        self.cpu_controller = MockDeviceController("cpu-1", "cpu")

        # Register them with the manager
        self.manager.register_monitor(self.gpu_monitor)
        self.manager.register_monitor(self.cpu_monitor)
        self.manager.register_controller(self.gpu_controller)
        self.manager.register_controller(self.cpu_controller)

    def test_register_devices(self):
        """Test registering devices with the manager."""
        assert "gpu:gpu-1" in self.manager.monitors
        assert "cpu:cpu-1" in self.manager.monitors
        assert "gpu:gpu-1" in self.manager.controllers
        assert "cpu:cpu-1" in self.manager.controllers

    def test_start_stop_all_monitors(self):
        """Test starting and stopping all monitors."""
        # Start all monitors
        self.manager.start_all_monitors()
        assert self.gpu_monitor.is_monitoring
        assert self.cpu_monitor.is_monitoring

        # Let them run briefly
        time.sleep(0.2)

        # Stop all monitors
        self.manager.stop_all_monitors()
        assert not self.gpu_monitor.is_monitoring
        assert not self.cpu_monitor.is_monitoring

    def test_get_device_status(self):
        """Test getting status of a specific device."""
        # Update status manually
        self.gpu_monitor.update_status()
        self.cpu_monitor.update_status()

        # Get status for GPU
        gpu_status = self.manager.get_device_status("gpu", "gpu-1")
        assert gpu_status["device_type"] == "gpu"
        assert gpu_status["device_id"] == "gpu-1"
        assert gpu_status["temperature"] == 30

        # Test nonexistent device
        assert self.manager.get_device_status("nonexistent", "device") is None

    def test_get_all_status(self):
        """Test getting status of all devices."""
        # Update status manually
        self.gpu_monitor.update_status()
        self.cpu_monitor.update_status()

        # Get all statuses
        all_status = self.manager.get_all_status()
        assert "gpu:gpu-1" in all_status
        assert "cpu:cpu-1" in all_status
        assert all_status["gpu:gpu-1"]["temperature"] == 30
        assert all_status["cpu:cpu-1"]["temperature"] == 30

    def test_apply_device_settings(self):
        """Test applying settings to a specific device."""
        # Apply settings to GPU
        result = self.manager.apply_device_settings("gpu", "gpu-1", {"fan_speed": 80})
        assert result is True
        assert self.gpu_controller.current_settings["fan_speed"] == 80

        # Test nonexistent device
        assert self.manager.apply_device_settings("nonexistent", "device", {}) is False
