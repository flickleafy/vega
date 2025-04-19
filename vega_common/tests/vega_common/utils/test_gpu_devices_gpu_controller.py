"""
Unit tests for the NvidiaGpuController class in gpu_devices.py.
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock

# Import the classes we're testing
from vega_common.utils.gpu_devices import NvidiaGpuController, NVMLError, _nvml_init_count


@pytest.fixture
def mock_pynvml():
    """Fixture to mock pynvml library."""
    with patch('vega_common.utils.gpu_devices.pynvml', autospec=True) as mock:
        # Setup common mocks
        mock.nvmlDeviceGetCount = MagicMock(return_value=2)  # Mock 2 GPUs
        mock.nvmlDeviceGetHandleByIndex = MagicMock()
        mock.nvmlDeviceGetName = MagicMock(return_value=b"NVIDIA GeForce RTX 3080")  # Return bytes as actual API does
        
        # Mock PCI info
        pci_info_mock = MagicMock()
        pci_info_mock.busId = b"0000:01:00.0"  # Return bytes as actual API does
        mock.nvmlDeviceGetPciInfo = MagicMock(return_value=pci_info_mock)
        
        # Mock fan functions
        mock.nvmlDeviceGetNumFans = MagicMock(return_value=2)
        mock.nvmlDeviceSetFanSpeed_v2 = MagicMock()
        mock.nvmlDeviceGetFanSpeed_v2 = MagicMock(side_effect=[60, 70])  # Default fan speeds
        
        # Define common NVML error constants
        mock.NVML_ERROR_NOT_SUPPORTED = 1
        mock.NVMLError = Exception  # Simple exception for testing
        
        yield mock


@pytest.fixture
def mock_initialize_nvml():
    """Fixture to mock the NVML initialization function."""
    with patch('vega_common.utils.gpu_devices._initialize_nvml_safe') as mock:
        yield mock


@pytest.fixture
def mock_shutdown_nvml():
    """Fixture to mock the NVML shutdown function."""
    with patch('vega_common.utils.gpu_devices._shutdown_nvml_safe') as mock:
        yield mock


class TestNvidiaGpuController:
    """Tests for the NvidiaGpuController class."""

    def test_initialization_success(self, mock_pynvml, mock_initialize_nvml, mock_shutdown_nvml):
        """Test successful initialization of the controller."""
        # Arrange
        device_index = 1
        
        # Act
        controller = NvidiaGpuController(device_index)
        
        # Assert
        assert controller.device_index == device_index
        assert controller.device_id == "0000:01:00.0"
        assert controller.device_type == "gpu"
        assert controller.device_name == "NVIDIA GeForce RTX 3080"
        mock_initialize_nvml.assert_called_once()
        mock_pynvml.nvmlDeviceGetCount.assert_called_once()
        mock_pynvml.nvmlDeviceGetHandleByIndex.assert_called_once_with(device_index)

    def test_initialization_with_invalid_index(self, mock_pynvml, mock_initialize_nvml, mock_shutdown_nvml):
        """Test initialization with invalid device index."""
        # Arrange
        mock_pynvml.nvmlDeviceGetCount.return_value = 2
        
        # Act & Assert - in the actual implementation, a ValueError is raised but then caught
        # and converted to an NVMLError, so we expect NVMLError here
        with pytest.raises(NVMLError):
            NvidiaGpuController(5)  # Index 5 should be out of range
        
        # Verify initialization was called once
        mock_initialize_nvml.assert_called_once()
        
        # Due to how the code is structured, shutdown is called twice:
        # 1. When the invalid index is detected
        # 2. Again in the exception handler
        assert mock_shutdown_nvml.call_count == 2

    def test_initialization_with_nvml_error(self, mock_pynvml, mock_initialize_nvml, mock_shutdown_nvml):
        """Test initialization when NVML raises an error."""
        # Arrange
        mock_pynvml.nvmlDeviceGetHandleByIndex.side_effect = mock_pynvml.NVMLError("NVML Error")
        
        # Act & Assert
        with pytest.raises(NVMLError):
            NvidiaGpuController(1)
        
        mock_initialize_nvml.assert_called_once()
        mock_shutdown_nvml.assert_called_once()

    def test_initialization_with_pynvml_none(self):
        """Test initialization when pynvml is None."""
        # Arrange
        with patch('vega_common.utils.gpu_devices.pynvml', None):
            # Act & Assert
            with pytest.raises(NVMLError):
                NvidiaGpuController(1)

    def test_set_fan_speed_success(self, mock_pynvml):
        """Test setting fan speed successfully for both fans."""
        # Arrange
        controller = NvidiaGpuController(0)
        
        # Act
        result = controller.set_fan_speed(50)
        
        # Assert
        assert result is True
        assert mock_pynvml.nvmlDeviceSetFanSpeed_v2.call_count == 2
        mock_pynvml.nvmlDeviceSetFanSpeed_v2.assert_any_call(controller.handle, 0, 50)
        mock_pynvml.nvmlDeviceSetFanSpeed_v2.assert_any_call(controller.handle, 1, 50)

    def test_set_fan_speed_with_different_values(self, mock_pynvml):
        """Test setting different speeds for two fans."""
        # Arrange
        controller = NvidiaGpuController(0)
        
        # Act
        result = controller.set_fan_speed(40, 60)
        
        # Assert
        assert result is True
        assert mock_pynvml.nvmlDeviceSetFanSpeed_v2.call_count == 2
        mock_pynvml.nvmlDeviceSetFanSpeed_v2.assert_any_call(controller.handle, 0, 40)
        mock_pynvml.nvmlDeviceSetFanSpeed_v2.assert_any_call(controller.handle, 1, 60)

    def test_set_fan_speed_clamp_values(self, mock_pynvml):
        """Test that fan speed values are clamped between 0 and 100."""
        # Arrange
        controller = NvidiaGpuController(0)
        
        # Act
        result = controller.set_fan_speed(-10, 110)
        
        # Assert
        assert result is True
        mock_pynvml.nvmlDeviceSetFanSpeed_v2.assert_any_call(controller.handle, 0, 0)  # Clamped to min
        mock_pynvml.nvmlDeviceSetFanSpeed_v2.assert_any_call(controller.handle, 1, 100)  # Clamped to max

    def test_set_fan_speed_one_fan_only(self, mock_pynvml):
        """Test setting fan speed when only one fan is present."""
        # Arrange
        mock_pynvml.nvmlDeviceGetNumFans.return_value = 1
        controller = NvidiaGpuController(0)
        
        # Act
        result = controller.set_fan_speed(50)
        
        # Assert
        assert result is True
        assert mock_pynvml.nvmlDeviceSetFanSpeed_v2.call_count == 1
        mock_pynvml.nvmlDeviceSetFanSpeed_v2.assert_called_with(controller.handle, 0, 50)

    def test_set_fan_speed_no_fans(self, mock_pynvml):
        """Test setting fan speed when no fans are present."""
        # Arrange
        mock_pynvml.nvmlDeviceGetNumFans.return_value = 0
        controller = NvidiaGpuController(0)
        
        # Act
        result = controller.set_fan_speed(50)
        
        # Assert
        assert result is True  # Should still succeed as no error is raised
        assert mock_pynvml.nvmlDeviceSetFanSpeed_v2.call_count == 0

    def test_set_fan_speed_fan0_not_supported(self, mock_pynvml):
        """Test setting fan speed when the first fan doesn't support speed control."""
        # Arrange
        controller = NvidiaGpuController(0)
        mock_pynvml.nvmlDeviceSetFanSpeed_v2.side_effect = [
            mock_pynvml.NVMLError(mock_pynvml.NVML_ERROR_NOT_SUPPORTED),  # Fan 0 not supported
            None  # Fan 1 succeeds
        ]
        
        # Act
        result = controller.set_fan_speed(50)
        
        # Assert
        assert result is True  # Should still succeed as this error is treated as a non-failure
        assert mock_pynvml.nvmlDeviceSetFanSpeed_v2.call_count == 2

    def test_set_fan_speed_fan1_not_supported(self, mock_pynvml):
        """Test setting fan speed when the second fan doesn't support speed control."""
        # Arrange
        controller = NvidiaGpuController(0)
        mock_pynvml.nvmlDeviceSetFanSpeed_v2.side_effect = [
            None,  # Fan 0 succeeds
            mock_pynvml.NVMLError(mock_pynvml.NVML_ERROR_NOT_SUPPORTED)  # Fan 1 not supported
        ]
        
        # Act
        result = controller.set_fan_speed(50)
        
        # Assert
        assert result is True  # Should still succeed as this error is treated as a non-failure
        assert mock_pynvml.nvmlDeviceSetFanSpeed_v2.call_count == 2

    def test_set_fan_speed_fan0_error(self, mock_pynvml):
        """Test setting fan speed when the first fan raises an error."""
        # Arrange
        controller = NvidiaGpuController(0)
        mock_pynvml.nvmlDeviceSetFanSpeed_v2.side_effect = [
            mock_pynvml.NVMLError("Fan 0 error"),  # Fan 0 fails with general error
            None  # Fan 1 succeeds
        ]
        
        # Act
        result = controller.set_fan_speed(50)
        
        # Assert
        assert result is False  # Should fail as an error occurred
        assert mock_pynvml.nvmlDeviceSetFanSpeed_v2.call_count == 2

    def test_set_fan_speed_fan1_error(self, mock_pynvml):
        """Test setting fan speed when the second fan raises an error."""
        # Arrange
        controller = NvidiaGpuController(0)
        mock_pynvml.nvmlDeviceSetFanSpeed_v2.side_effect = [
            None,  # Fan 0 succeeds
            mock_pynvml.NVMLError("Fan 1 error")  # Fan 1 fails with general error
        ]
        
        # Act
        result = controller.set_fan_speed(50)
        
        # Assert
        assert result is False  # Should fail as an error occurred
        assert mock_pynvml.nvmlDeviceSetFanSpeed_v2.call_count == 2

    def test_set_fan_speed_general_nvml_error(self, mock_pynvml):
        """Test setting fan speed when a general NVML error occurs."""
        # Arrange
        controller = NvidiaGpuController(0)
        mock_pynvml.nvmlDeviceGetNumFans.side_effect = mock_pynvml.NVMLError("General NVML error")
        
        # Act
        result = controller.set_fan_speed(50)
        
        # Assert
        assert result is False
        assert mock_pynvml.nvmlDeviceSetFanSpeed_v2.call_count == 0

    def test_set_fan_speed_no_handle(self):
        """Test setting fan speed when handle is None."""
        # Arrange - create a controller instance without going through the normal initialization
        with patch('vega_common.utils.gpu_devices.pynvml'):
            with patch('vega_common.utils.gpu_devices._initialize_nvml_safe'):
                # Create a controller and manually set handle to None
                controller = NvidiaGpuController.__new__(NvidiaGpuController)
                controller.device_id = "test_gpu"
                controller.device_name = "Test GPU"
                controller.handle = None
                
                # Act
                result = controller.set_fan_speed(50)
                
                # Assert
                assert result is False

    def test_apply_settings_int_fan_speed(self, mock_pynvml):
        """Test applying settings with an integer fan speed (same for both fans)."""
        # Arrange
        controller = NvidiaGpuController(0)
        settings = {'fan_speed': 75}
        
        # Patch set_fan_speed to track calls and return True
        with patch.object(controller, 'set_fan_speed') as mock_set_fan_speed:
            mock_set_fan_speed.return_value = True
            
            # Act
            result = controller.apply_settings(settings)
            
            # Assert
            assert result is True
            mock_set_fan_speed.assert_called_once_with(75)

    def test_apply_settings_tuple_fan_speed(self, mock_pynvml):
        """Test applying settings with a tuple of fan speeds (different for each fan)."""
        # Arrange
        controller = NvidiaGpuController(0)
        settings = {'fan_speed': (60, 80)}
        
        # Patch set_fan_speed to track calls and return True
        with patch.object(controller, 'set_fan_speed') as mock_set_fan_speed:
            mock_set_fan_speed.return_value = True
            
            # Act
            result = controller.apply_settings(settings)
            
            # Assert
            assert result is True
            mock_set_fan_speed.assert_called_once_with(60, 80)

    def test_apply_settings_list_fan_speed(self, mock_pynvml):
        """Test applying settings with a list of fan speeds (different for each fan)."""
        # Arrange
        controller = NvidiaGpuController(0)
        settings = {'fan_speed': [40, 90]}
        
        # Patch set_fan_speed to track calls and return True
        with patch.object(controller, 'set_fan_speed') as mock_set_fan_speed:
            mock_set_fan_speed.return_value = True
            
            # Act
            result = controller.apply_settings(settings)
            
            # Assert
            assert result is True
            mock_set_fan_speed.assert_called_once_with(40, 90)

    def test_apply_settings_float_fan_speed(self, mock_pynvml):
        """Test applying settings with a float fan speed (should convert to int)."""
        # Arrange
        controller = NvidiaGpuController(0)
        settings = {'fan_speed': 50.5}
        
        # Patch set_fan_speed to track calls and return True
        with patch.object(controller, 'set_fan_speed') as mock_set_fan_speed:
            mock_set_fan_speed.return_value = True
            
            # Act
            result = controller.apply_settings(settings)
            
            # Assert
            assert result is True
            mock_set_fan_speed.assert_called_once_with(50)  # Should be converted to int

    def test_apply_settings_invalid_fan_speed_format(self, mock_pynvml):
        """Test applying settings with an invalid fan speed format."""
        # Arrange
        controller = NvidiaGpuController(0)
        settings = {'fan_speed': "50%"}  # String is invalid format
        
        # Patch set_fan_speed to ensure it's not called
        with patch.object(controller, 'set_fan_speed') as mock_set_fan_speed:
            # Act
            result = controller.apply_settings(settings)
            
            # Assert
            assert result is False
            mock_set_fan_speed.assert_not_called()

    def test_apply_settings_empty_tuple_fan_speed(self, mock_pynvml):
        """Test applying settings with an empty tuple fan speed (invalid format)."""
        # Arrange
        controller = NvidiaGpuController(0)
        settings = {'fan_speed': ()}  # Empty tuple is invalid
        
        # Patch set_fan_speed to ensure it's not called
        with patch.object(controller, 'set_fan_speed') as mock_set_fan_speed:
            # Act
            result = controller.apply_settings(settings)
            
            # Assert
            assert result is False
            mock_set_fan_speed.assert_not_called()

    def test_apply_settings_single_value_tuple(self, mock_pynvml):
        """Test applying settings with a single-value tuple (invalid format for two fans)."""
        # Arrange
        controller = NvidiaGpuController(0)
        settings = {'fan_speed': (50,)}  # Single value tuple is invalid for the method
        
        # Patch set_fan_speed to ensure it's not called with tuple
        with patch.object(controller, 'set_fan_speed') as mock_set_fan_speed:
            # Act
            result = controller.apply_settings(settings)
            
            # Assert
            assert result is False
            mock_set_fan_speed.assert_not_called()

    def test_apply_settings_failure(self, mock_pynvml):
        """Test applying settings when set_fan_speed fails."""
        # Arrange
        controller = NvidiaGpuController(0)
        settings = {'fan_speed': 50}
        
        # Patch set_fan_speed to return False (failure)
        with patch.object(controller, 'set_fan_speed') as mock_set_fan_speed:
            mock_set_fan_speed.return_value = False
            
            # Act
            result = controller.apply_settings(settings)
            
            # Assert
            assert result is False
            mock_set_fan_speed.assert_called_once_with(50)

    def test_apply_settings_no_recognized_settings(self, mock_pynvml):
        """Test applying settings with no recognized settings."""
        # Arrange
        controller = NvidiaGpuController(0)
        settings = {'unknown_setting': 'value'}
        
        # Act
        result = controller.apply_settings(settings)
        
        # Assert
        assert result is False  # Should return False if no settings were recognized

    def test_apply_settings_empty_dict(self, mock_pynvml):
        """Test applying settings with an empty dictionary."""
        # Arrange
        controller = NvidiaGpuController(0)
        settings = {}
        
        # Act
        result = controller.apply_settings(settings)
        
        # Assert
        assert result is False  # Should return False if no settings were provided

    def test_apply_settings_no_handle(self):
        """Test applying settings when handle is None."""
        # Arrange - create a controller instance without going through the normal initialization
        with patch('vega_common.utils.gpu_devices.pynvml'):
            with patch('vega_common.utils.gpu_devices._initialize_nvml_safe'):
                # Create a controller and manually set handle to None
                controller = NvidiaGpuController.__new__(NvidiaGpuController)
                controller.device_id = "test_gpu"
                controller.device_name = "Test GPU"
                controller.handle = None
                
                # Act
                result = controller.apply_settings({'fan_speed': 50})
                
                # Assert
                assert result is False

    def test_get_available_settings_success(self, mock_pynvml):
        """Test getting available settings successfully."""
        # Arrange
        controller = NvidiaGpuController(0)
        
        # Act
        settings = controller.get_available_settings()
        
        # Assert
        assert settings['device_name'] == "NVIDIA GeForce RTX 3080"
        assert settings['device_id'] == "0000:01:00.0"
        assert "fan_speed" in settings['controllable_settings']
        assert settings['current_fan_speeds'] == [60, 70]  # From the mock setup
        assert settings['num_fans'] == 2

    def test_get_available_settings_no_fans(self, mock_pynvml):
        """Test getting available settings when no fans are present."""
        # Arrange
        controller = NvidiaGpuController(0)
        mock_pynvml.nvmlDeviceGetNumFans.return_value = 0
        
        # Act
        settings = controller.get_available_settings()
        
        # Assert
        assert settings['current_fan_speeds'] == []
        assert settings['num_fans'] == 0

    def test_get_available_settings_nvml_error(self, mock_pynvml):
        """Test getting available settings when NVML raises an error."""
        # Arrange
        controller = NvidiaGpuController(0)
        mock_pynvml.nvmlDeviceGetNumFans.side_effect = mock_pynvml.NVMLError("NVML Error")
        
        # Act
        settings = controller.get_available_settings()
        
        # Assert
        assert settings['current_fan_speeds'] == []
        assert settings['num_fans'] == 0

    def test_get_available_settings_no_handle(self):
        """Test getting available settings when handle is None."""
        # Arrange - create a controller instance without going through the normal initialization
        with patch('vega_common.utils.gpu_devices.pynvml'):
            with patch('vega_common.utils.gpu_devices._initialize_nvml_safe'):
                # Create a controller and manually set handle to None
                controller = NvidiaGpuController.__new__(NvidiaGpuController)
                controller.device_id = "test_gpu"
                controller.device_name = "Test GPU"
                controller.handle = None
                
                # Act
                settings = controller.get_available_settings()
                
                # Assert
                assert settings['device_name'] == "Test GPU"
                assert settings['device_id'] == "test_gpu"
                assert "fan_speed" in settings['controllable_settings']
                assert 'current_fan_speeds' not in settings  # Should not be present when handle is None
                assert 'num_fans' not in settings

    def test_cleanup(self, mock_pynvml, mock_shutdown_nvml):
        """Test cleanup method."""
        # Arrange
        controller = NvidiaGpuController(0)
        
        # Act
        controller.cleanup()
        
        # Assert
        mock_shutdown_nvml.assert_called_once()


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])

