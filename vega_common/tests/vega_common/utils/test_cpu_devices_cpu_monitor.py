"""
Unit tests for the CpuMonitor class in cpu_devices.py.
"""
import pytest
from unittest.mock import patch, MagicMock
import psutil

# Import CpuMonitor from cpu_devices
from vega_common.utils.cpu_devices import CpuMonitor
from vega_common.utils.device_status import DeviceStatus

# Mock sensor data structure similar to psutil.sensors_temperatures()
MOCK_TEMPS_CORETEMP = {
    'coretemp': [
        psutil._common.shwtemp(label='Package id 0', current=55.0, high=85.0, critical=100.0),
        psutil._common.shwtemp(label='Core 0', current=52.0, high=85.0, critical=100.0),
        psutil._common.shwtemp(label='Core 1', current=53.0, high=85.0, critical=100.0),
    ]
}

MOCK_TEMPS_K10TEMP = {
    'k10temp': [
        psutil._common.shwtemp(label='Tctl', current=60.5, high=None, critical=None),
        psutil._common.shwtemp(label='Tdie', current=60.5, high=None, critical=None),
    ]
}

MOCK_TEMPS_MULTIPLE = {
    'k10temp': [
        psutil._common.shwtemp(label='Tctl', current=55.5, high=100.0, critical=100.0),
        psutil._common.shwtemp(label='Tdie', current=54.0, high=None, critical=None),
        psutil._common.shwtemp(label='Tccd1', current=56.0, high=None, critical=None),
    ],
    'coretemp': [
        psutil._common.shwtemp(label='Package id 0', current=58.0, high=85.0, critical=100.0),
        psutil._common.shwtemp(label='Core 0', current=57.5, high=85.0, critical=100.0),
    ]
}

# Mock with non-preferred labels but preferred devices
MOCK_TEMPS_FALLBACK = {
    'k10temp': [
        psutil._common.shwtemp(label='Unknown Label', current=65.0, high=None, critical=None),
    ],
    'unknown_device': [
        psutil._common.shwtemp(label='Package id 0', current=70.0, high=85.0, critical=100.0),
    ]
}

# Mock with None label
MOCK_TEMPS_NONE_LABEL = {
    'k10temp': [
        psutil._common.shwtemp(label=None, current=62.5, high=None, critical=None),
    ]
}

MOCK_TEMPS_EMPTY = {}

MOCK_TEMPS_MISSING_CURRENT = {
    'coretemp': [
        psutil._common.shwtemp(label='Package id 0', current=None, high=85.0, critical=100.0), # Missing 'current'
    ]
}


@pytest.fixture
def mock_psutil():
    """Fixture to mock psutil functions."""
    with patch('vega_common.utils.cpu_devices.psutil', autospec=True) as mock_psutil_module:
        # Mock sensors_temperatures if it exists in the real psutil
        if hasattr(psutil, 'sensors_temperatures'):
            mock_psutil_module.sensors_temperatures.return_value = MOCK_TEMPS_CORETEMP
        else:
            # If the real psutil doesn't have it, make the mock reflect that
            delattr(mock_psutil_module, 'sensors_temperatures')

        # Mock the _common attribute if needed for shwtemp
        if hasattr(psutil, '_common'):
             mock_psutil_module._common = psutil._common

        yield mock_psutil_module


@pytest.fixture
def cpu_monitor(mock_psutil):
    """Fixture to create a CpuMonitor instance with mocked psutil."""
    # Use default parameters
    monitor = CpuMonitor(device_id="cpu_main", monitoring_interval=0.1)
    return monitor


class TestCpuMonitor:
    """Tests for the CpuMonitor class."""

    def test_initialization(self, cpu_monitor):
        """Test basic initialization."""
        assert cpu_monitor.device_id == "cpu_main"
        assert cpu_monitor.device_type == "cpu"
        assert isinstance(cpu_monitor.status, DeviceStatus)
        # Register temperature tracking property
        cpu_monitor.status.register_tracked_property("temperature")
        assert "temperature" in cpu_monitor.status.status_history
        assert cpu_monitor.cpu_temp_sensor_labels is not None
        assert cpu_monitor.cpu_temp_device_names is not None

    def test_initialization_custom_params(self, mock_psutil):
        """Test initialization with custom parameters."""
        custom_labels = ["custom_label1", "custom_label2"]
        custom_devices = ["custom_device1", "custom_device2"]
        
        monitor = CpuMonitor(
            device_id="custom_cpu", 
            monitoring_interval=2.5,
            cpu_temp_sensor_labels=custom_labels,
            cpu_temp_device_names=custom_devices
        )
        
        assert monitor.device_id == "custom_cpu"
        assert abs(monitor.monitoring_interval - 2.5) < 1e-6
        assert monitor.cpu_temp_sensor_labels == custom_labels
        assert monitor.cpu_temp_device_names == custom_devices

    def test_update_status_success(self, cpu_monitor, mock_psutil):
        """Test successful status update with coretemp sensor."""
        mock_psutil.sensors_temperatures.return_value = MOCK_TEMPS_CORETEMP
        
        cpu_monitor.update_status()
        status = cpu_monitor.status
        
        # Should find the Package id 0 temperature
        assert abs(status.get_property("temperature") - 55.0) < 1e-6
        assert not status.has_error("temperature")

    def test_update_status_k10temp(self, cpu_monitor, mock_psutil):
        """Test finding temperature with k10temp sensor."""
        mock_psutil.sensors_temperatures.return_value = MOCK_TEMPS_K10TEMP
        
        cpu_monitor.update_status()
        status = cpu_monitor.status
        
        # Should prioritize Tdie over Tctl
        assert abs(status.get_property("temperature") - 60.5) < 1e-6
        assert not status.has_error("temperature")

    def test_update_status_multiple_devices(self, cpu_monitor, mock_psutil):
        """Test finding temperature with multiple devices available."""
        mock_psutil.sensors_temperatures.return_value = MOCK_TEMPS_MULTIPLE
        
        cpu_monitor.update_status()
        status = cpu_monitor.status
        
        # Should prioritize based on device and label
        assert abs(status.get_property("temperature") - 54.0) < 1e-6  # k10temp/Tdie should be selected
        assert not status.has_error("temperature")

    def test_update_status_sensor_not_found(self, cpu_monitor, mock_psutil):
        """Test status update when no sensors are found."""
        mock_psutil.sensors_temperatures.return_value = MOCK_TEMPS_EMPTY
        
        cpu_monitor.update_status()
        status = cpu_monitor.status
        
        assert status.get_property("temperature") is None
        assert status.has_error("temperature")
        assert "Could not find a suitable CPU temperature sensor" in status.get_error("temperature")

    def test_update_status_psutil_exception_temp(self, cpu_monitor, mock_psutil):
        """Test status update when psutil.sensors_temperatures raises an exception."""
        mock_psutil.sensors_temperatures.side_effect = RuntimeError("Test Exception Temp")
        
        cpu_monitor.update_status()
        status = cpu_monitor.status
        
        assert status.get_property("temperature") is None
        assert status.has_error("temperature")
        assert "Error reading psutil sensors" in status.get_error("temperature")

    def test_update_status_no_sensors_temperatures_support(self, cpu_monitor, mock_psutil):
        """Test behavior when psutil doesn't support sensors_temperatures."""
        if hasattr(mock_psutil, 'sensors_temperatures'):
            delattr(mock_psutil, 'sensors_temperatures')
        
        cpu_monitor.update_status()
        status = cpu_monitor.status
        
        assert status.get_property("temperature") is None
        assert status.has_error("temperature") or status.has_error("initialization")
        
    def test_find_cpu_temp_missing_current(self, cpu_monitor, mock_psutil):
        """Test temperature search when 'current' attribute is missing."""
        mock_psutil.sensors_temperatures.return_value = MOCK_TEMPS_MISSING_CURRENT
        
        cpu_monitor.update_status()
        status = cpu_monitor.status
        
        # Should not find a temperature
        assert status.get_property("temperature") is None
        assert status.has_error("temperature")

    def test_get_cpu_temperature_convenience_method(self, cpu_monitor, mock_psutil):
        """Test the convenience method get_cpu_temperature."""
        mock_psutil.sensors_temperatures.return_value = MOCK_TEMPS_K10TEMP
        
        cpu_monitor.update_status()
        
        # Check the convenience method
        assert abs(cpu_monitor.get_cpu_temperature() - 60.5) < 1e-6

    def test_custom_sensor_label_priority(self, mock_psutil):
        """Test that custom sensor label priorities work correctly."""
        mock_psutil.sensors_temperatures.return_value = MOCK_TEMPS_MULTIPLE
        
        # Create monitor with custom priority that prefers Tccd1
        monitor = CpuMonitor(
            device_id="custom_cpu",
            cpu_temp_sensor_labels=["tccd1", "tdie", "package"]
        )
        
        monitor.update_status()
        
        # Should prioritize based on custom priority order
        assert abs(monitor.get_cpu_temperature() - 56.0) < 1e-6  # k10temp/Tccd1 based on priority
        
    def test_fallback_to_any_sensor_in_preferred_device(self, mock_psutil):
        """Test fallback to any sensor in preferred device when no preferred label is found."""
        mock_psutil.sensors_temperatures.return_value = MOCK_TEMPS_FALLBACK
        
        monitor = CpuMonitor(device_id="fallback_cpu")
        monitor.update_status()
        
        # Should fall back to "Unknown Label" from k10temp since it's in preferred devices
        assert abs(monitor.get_cpu_temperature() - 65.0) < 1e-6
        assert not monitor.status.has_error("temperature")
        
    def test_sensor_with_none_label(self, mock_psutil):
        """Test handling sensors with None label."""
        mock_psutil.sensors_temperatures.return_value = MOCK_TEMPS_NONE_LABEL
        
        monitor = CpuMonitor(device_id="none_label_cpu")
        monitor.update_status()
        
        # Should handle None label gracefully and still find a temperature
        assert abs(monitor.get_cpu_temperature() - 62.5) < 1e-6
        
    def test_repeated_error_handling(self, cpu_monitor, mock_psutil):
        """Test that errors are only logged once if they persist."""
        # First update with error
        mock_psutil.sensors_temperatures.return_value = MOCK_TEMPS_EMPTY
        cpu_monitor.update_status()
        assert cpu_monitor.status.has_error("temperature")
        
        # Second update with same error shouldn't set the error again
        with patch('logging.warning') as mock_warning:
            cpu_monitor.update_status()
            # The warning should not be called again for the same error
            assert not mock_warning.called
            
    def test_psutil_none_initialization(self):
        """Test initialization when psutil is None."""
        with patch('vega_common.utils.cpu_devices.psutil', None):
            monitor = CpuMonitor(device_id="no_psutil_cpu")
            assert monitor.status.has_error("initialization")
            
            # Update status should handle psutil=None gracefully
            monitor.update_status()
            assert monitor.get_cpu_temperature() is None
            
    def test_non_preferred_device_with_preferred_label(self, mock_psutil):
        """Test finding temperature in non-preferred device with preferred label."""
        # Mock data with a preferred label (package) but in a non-preferred device
        mock_data = {
            'non_preferred_device': [
                psutil._common.shwtemp(label='Package id 0', current=72.0, high=85.0, critical=100.0),
            ]
        }
        mock_psutil.sensors_temperatures.return_value = mock_data
        
        # Check if the current implementation should find temperatures from non-preferred devices
        # with preferred labels (Strategy 2 in the implementation comments)
        monitor = CpuMonitor(device_id="non_preferred_cpu")
        monitor.update_status()
        
        # The current implementation doesn't search for preferred labels in non-preferred devices
        # so we expect temperature to be None
        assert monitor.get_cpu_temperature() is None
        assert monitor.status.has_error("temperature")
        assert "Could not find a suitable CPU temperature sensor" in monitor.status.get_error("temperature")
        
    def test_label_normalization(self, mock_psutil):
        """Test that sensor labels are properly normalized."""
        # Test with a label that needs normalization (spaces and capitalization)
        mock_data = {
            'k10temp': [
                psutil._common.shwtemp(label='Core 0', current=58.5, high=None, critical=None),
                psutil._common.shwtemp(label='PACKAGE ID 0', current=59.0, high=None, critical=None),
            ]
        }
        mock_psutil.sensors_temperatures.return_value = mock_data
        
        # Set up monitor with label priorities that match normalized forms
        monitor = CpuMonitor(
            device_id="normalize_cpu",
            cpu_temp_sensor_labels=["package_id_0", "core_0"]
        )
        monitor.update_status()
        
        # Should match "PACKAGE ID 0" to "package_id_0" and prioritize it
        assert abs(monitor.get_cpu_temperature() - 59.0) < 1e-6
        
    def test_clear_error_on_success(self, cpu_monitor, mock_psutil):
        """Test that errors are cleared when a successful reading occurs."""
        # First set an error
        mock_psutil.sensors_temperatures.return_value = MOCK_TEMPS_EMPTY
        cpu_monitor.update_status()
        assert cpu_monitor.status.has_error("temperature")
        
        # Then get a successful reading
        mock_psutil.sensors_temperatures.return_value = MOCK_TEMPS_CORETEMP
        cpu_monitor.update_status()
        
        # Error should be cleared
        assert not cpu_monitor.status.has_error("temperature")
        assert abs(cpu_monitor.get_cpu_temperature() - 55.0) < 1e-6

    def test_cleanup_method(self, cpu_monitor):
        """Test the cleanup method is called without errors."""
        # Simply verify that cleanup runs without exceptions
        cpu_monitor.cleanup()
        # No assertions needed - just checking for no exceptions
        
    def test_empty_sensors_in_device(self, mock_psutil):
        """Test handling a device with an empty sensor list."""
        mock_psutil.sensors_temperatures.return_value = {'coretemp': []}
        
        monitor = CpuMonitor(device_id="empty_sensors_cpu")
        monitor.update_status()
        
        # Should handle empty sensors gracefully
        assert monitor.get_cpu_temperature() is None
        assert monitor.status.has_error("temperature")
        
    def test_generic_temp_label_fallback(self, mock_psutil):
        """Test fallback to generic temperature labels like 'temp1'."""
        # Create mock with only generic temperature labels
        mock_data = {
            'acpitz': [
                psutil._common.shwtemp(label='temp1', current=45.0, high=95.0, critical=105.0),
                psutil._common.shwtemp(label='temp2', current=47.0, high=95.0, critical=105.0),
            ]
        }
        mock_psutil.sensors_temperatures.return_value = mock_data
        
        monitor = CpuMonitor(device_id="generic_temp_cpu")
        monitor.update_status()
        
        # Should find the generic temperature
        assert abs(monitor.get_cpu_temperature() - 45.0) < 1e-6
        
    def test_temperature_history_tracking(self, cpu_monitor, mock_psutil):
        """Test that temperature history is properly tracked."""
        # Register temperature tracking property if not already done
        if "temperature" not in cpu_monitor.status.status_history:
            cpu_monitor.status.register_tracked_property("temperature", default_value=0.0)
        
        # Update with different temperatures
        mock_psutil.sensors_temperatures.return_value = MOCK_TEMPS_CORETEMP
        cpu_monitor.update_status()  # First update: 55.0
        
        # Change the temperature for next update
        new_data = {
            'coretemp': [
                psutil._common.shwtemp(label='Package id 0', current=57.0, high=85.0, critical=100.0),
            ]
        }
        mock_psutil.sensors_temperatures.return_value = new_data
        cpu_monitor.update_status()  # Second update: 57.0
        
        # Check history
        history = cpu_monitor.status.get_property_history("temperature")
        assert len(history) > 0
        assert 55.0 in history
        assert 57.0 in history
        
    def test_extreme_temperature_values(self, mock_psutil):
        """Test handling of extreme temperature values."""
        # Test with very high temperature
        mock_high = {
            'coretemp': [
                psutil._common.shwtemp(label='Package id 0', current=999.0, high=None, critical=None),
            ]
        }
        mock_psutil.sensors_temperatures.return_value = mock_high
        
        monitor = CpuMonitor(device_id="extreme_temp_cpu")
        monitor.update_status()
        assert abs(monitor.get_cpu_temperature() - 999.0) < 1e-6
        
        # Test with very low temperature
        mock_low = {
            'coretemp': [
                psutil._common.shwtemp(label='Package id 0', current=-50.0, high=None, critical=None),
            ]
        }
        mock_psutil.sensors_temperatures.return_value = mock_low
        monitor.update_status()
        assert abs(monitor.get_cpu_temperature() - (-50.0)) < 1e-6
        
        # Test with zero temperature
        mock_zero = {
            'coretemp': [
                psutil._common.shwtemp(label='Package id 0', current=0.0, high=None, critical=None),
            ]
        }
        mock_psutil.sensors_temperatures.return_value = mock_zero
        monitor.update_status()
        assert abs(monitor.get_cpu_temperature() - 0.0) < 1e-6
        
    def test_sensors_with_no_high_critical(self, mock_psutil):
        """Test sensors that don't have high or critical values."""
        mock_data = {
            'k10temp': [
                psutil._common.shwtemp(label='Tdie', current=65.5, high=None, critical=None),
            ]
        }
        mock_psutil.sensors_temperatures.return_value = mock_data
        
        monitor = CpuMonitor(device_id="no_high_critical_cpu")
        monitor.update_status()
        
        # Should handle missing high/critical values gracefully
        assert abs(monitor.get_cpu_temperature() - 65.5) < 1e-6
        
    def test_sorting_by_label_priority(self, mock_psutil):
        """Test that sensors are sorted by label priority correctly."""
        # Create a mock with multiple sensors in non-priority order
        mock_data = {
            'k10temp': [
                psutil._common.shwtemp(label='Tccd1', current=62.0, high=None, critical=None),
                psutil._common.shwtemp(label='Tctl', current=63.0, high=None, critical=None),
                psutil._common.shwtemp(label='Tdie', current=61.0, high=None, critical=None),
            ]
        }
        mock_psutil.sensors_temperatures.return_value = mock_data
        
        # Create monitor with specific priority order
        monitor = CpuMonitor(
            device_id="sort_priority_cpu",
            cpu_temp_sensor_labels=["tdie", "tctl", "tccd1"]
        )
        monitor.update_status()
        
        # Should select Tdie based on priority, even though it's not first in the list
        assert abs(monitor.get_cpu_temperature() - 61.0) < 1e-6
        
    def test_init_count_safety(self, mock_psutil):
        """Test the safety of initialization and cleanup."""
        # Simulate multiple monitors starting and stopping
        monitor1 = CpuMonitor(device_id="cpu1")
        monitor2 = CpuMonitor(device_id="cpu2")
        
        # Both monitors should initialize successfully
        assert monitor1.device_id == "cpu1"
        assert monitor2.device_id == "cpu2"
        
        # Both should cleanup without errors
        monitor1.cleanup()
        monitor2.cleanup()
        
        # Create another one after cleanup to ensure init works again
        monitor3 = CpuMonitor(device_id="cpu3")
        assert monitor3.device_id == "cpu3"
        monitor3.cleanup()
        
    def test_has_sensors_temperatures_attribute_check(self, cpu_monitor, mock_psutil):
        """Test the check for the presence of sensors_temperatures attribute."""
        # Test with attribute present but raising exception
        mock_psutil.sensors_temperatures.side_effect = AttributeError("Test Exception")
        
        cpu_monitor.update_status()
        
        # Should handle missing attribute gracefully
        assert cpu_monitor.get_cpu_temperature() is None
        assert cpu_monitor.status.has_error("temperature")
        
        # Simulate sensors_temperatures not existing
        if hasattr(mock_psutil, 'sensors_temperatures'):
            delattr(mock_psutil, 'sensors_temperatures')
            
        # Create a new monitor in this state
        monitor = CpuMonitor(device_id="no_sensors_temp_cpu")
        assert monitor.status.has_error("initialization")
        
    def test_non_preferred_device_only(self, mock_psutil):
        """Test when only non-preferred devices are available."""
        mock_data = {
            'unknown_device': [
                psutil._common.shwtemp(label='temp1', current=48.0, high=None, critical=None),
            ]
        }
        mock_psutil.sensors_temperatures.return_value = mock_data
        
        # Create monitor with custom device preference that doesn't include the available device
        monitor = CpuMonitor(
            device_id="non_preferred_device_cpu",
            cpu_temp_device_names=["k10temp", "coretemp"]
        )
        monitor.update_status()
        
        # Should not find a temperature because device isn't in preferred list
        assert monitor.get_cpu_temperature() is None

