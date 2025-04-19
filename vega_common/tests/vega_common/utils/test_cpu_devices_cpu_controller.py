import sys
import os
import io
import logging
import tempfile
from typing import Dict, List, Any, Optional

import pytest
from unittest.mock import MagicMock, patch

# Import CpuMonitor from cpu_devices
from vega_common.utils.cpu_devices import CpuController
from vega_common.utils.device_status import DeviceStatus

# Define the list of power plans used in the tests
POWER_PLANS = ["powersave", "schedutil", "performance"]

@pytest.fixture
def mock_sub_process():
    """Create a mock for subprocess operations."""
    with patch("vega_common.utils.cpu_devices.sub_process") as mock:
        mock.run_cmd = MagicMock()
        yield mock

@pytest.fixture
def mock_process_utils():
    """Create a mock for process utilities."""
    with patch("vega_common.utils.cpu_devices.detect_performance_apps") as perf_mock:
        with patch("vega_common.utils.cpu_devices.detect_balance_apps") as bal_mock:
            with patch("vega_common.utils.cpu_devices.get_process_list") as proc_mock:
                mocks = {
                    "detect_performance_apps": perf_mock,
                    "detect_balance_apps": bal_mock,
                    "get_process_list": proc_mock
                }
                perf_mock.return_value = False
                bal_mock.return_value = False
                yield mocks

class TestCpuController:
    """Tests for the CpuController class."""

    def test_init_default(self):
        """Test initialization with default device ID."""
        controller = CpuController()
        assert controller.device_id == "cpu_main"
        assert controller.device_type == "cpu"

    def test_init_custom(self):
        """Test initialization with custom device ID."""
        controller = CpuController(device_id="custom_cpu")
        assert controller.device_id == "custom_cpu"
        assert controller.device_type == "cpu"

    def test_run_cpu_command_success(self, mock_sub_process):
        """Test _run_cpu_command with successful execution."""
        mock_sub_process.run_cmd.return_value = "command output"
        
        controller = CpuController()
        result = controller._run_cpu_command(["echo", "test"])
        
        assert result == "command output"
        mock_sub_process.run_cmd.assert_called_once()

    def test_run_cpu_command_with_shell(self, mock_sub_process):
        """Test _run_cpu_command with shell=True."""
        mock_sub_process.run_cmd.return_value = "shell command output"
        
        controller = CpuController()
        result = controller._run_cpu_command(["echo test"], use_shell=True)
        
        assert result == "shell command output"
        mock_sub_process.run_cmd.assert_called_once_with("echo test", use_shell=True)

    def test_run_cpu_command_exception(self, mock_sub_process):
        """Test _run_cpu_command handling exceptions."""
        mock_sub_process.run_cmd.side_effect = Exception("Command failed")
        
        controller = CpuController()
        result = controller._run_cpu_command(["echo", "test"])
        
        assert result is None
        mock_sub_process.run_cmd.assert_called_once()

    def test_run_cpu_command_exception_with_mock_attr(self, mock_sub_process):
        """Test _run_cpu_command handling exceptions when sub_process has mock_run_cmd attribute."""
        mock_sub_process.run_cmd.side_effect = Exception("Command failed")
        # Add mock_run_cmd attribute to simulate test environment
        setattr(mock_sub_process, 'mock_run_cmd', True)
        
        controller = CpuController()
        result = controller._run_cpu_command(["echo", "test"])
        
        assert result is None
        mock_sub_process.run_cmd.assert_called_once()

    def test_set_power_plan_valid(self, mock_sub_process):
        """Test set_power_plan with a valid plan."""
        # Setup mock to return success for command and matching plan for verification
        mock_sub_process.run_cmd.return_value = "success"
        
        controller = CpuController()
        
        # Mock get_current_power_plan to return the plan we're setting
        controller.get_current_power_plan = MagicMock(return_value="performance")
        
        # Test set_power_plan
        result = controller.set_power_plan("performance")
        
        # Verify behavior and outcome
        assert result is True
        mock_sub_process.run_cmd.assert_called_once()
        controller.get_current_power_plan.assert_called_once()

    def test_set_power_plan_invalid(self, mock_sub_process):
        """Test set_power_plan with an invalid plan."""
        controller = CpuController()
        result = controller.set_power_plan("invalid_plan")
        
        assert result is False
        mock_sub_process.run_cmd.assert_not_called()

    def test_set_power_plan_command_failed(self, mock_sub_process):
        """Test set_power_plan when command execution fails."""
        mock_sub_process.run_cmd.return_value = None  # Command failed
        
        controller = CpuController()
        result = controller.set_power_plan("performance")
        
        assert result is False
        mock_sub_process.run_cmd.assert_called_once()

    def test_set_power_plan_verification_failed(self, mock_sub_process):
        """Test set_power_plan when verification fails."""
        mock_sub_process.run_cmd.return_value = "success"  # Command succeeded
        
        controller = CpuController()
        # Mock get_current_power_plan to return a different plan
        controller.get_current_power_plan = MagicMock(return_value="powersave")
        
        result = controller.set_power_plan("performance")
        
        assert result is False
        mock_sub_process.run_cmd.assert_called_once()
        controller.get_current_power_plan.assert_called_once()

    def test_set_power_plan_mock_run_cmd_attribute(self, mock_sub_process):
        """Test set_power_plan when command fails but mock_run_cmd attribute exists."""
        mock_sub_process.run_cmd.return_value = None  # Command failed
        # Add mock_run_cmd attribute to simulate test environment
        setattr(mock_sub_process, 'mock_run_cmd', True)
        
        controller = CpuController()
        result = controller.set_power_plan("performance")
        
        # Should return False when result is None, even with mock_run_cmd attribute
        assert result is False
        mock_sub_process.run_cmd.assert_called_once()

    def test_get_current_power_plan_success(self, mock_sub_process):
        """Test get_current_power_plan with successful execution."""
        mock_sub_process.run_cmd.return_value = "performance"
        
        controller = CpuController()
        result = controller.get_current_power_plan()
        
        assert result == "performance"
        mock_sub_process.run_cmd.assert_called_once()

    def test_get_current_power_plan_failure(self, mock_sub_process):
        """Test get_current_power_plan when command fails."""
        mock_sub_process.run_cmd.return_value = None
        
        controller = CpuController()
        result = controller.get_current_power_plan()
        
        assert result is None
        mock_sub_process.run_cmd.assert_called_once()

    def test_get_current_power_plan_unknown(self, mock_sub_process):
        """Test get_current_power_plan returns unknown plan."""
        mock_sub_process.run_cmd.return_value = "unknown_plan"
        
        controller = CpuController()
        result = controller.get_current_power_plan()
        
        assert result == "unknown_plan"
        mock_sub_process.run_cmd.assert_called_once()

    def test_get_current_power_plan_unknown_plan(self, mock_sub_process):
        """Test get_current_power_plan returning a plan not in POWER_PLANS."""
        mock_sub_process.run_cmd.return_value = "custom_plan"  # Plan not in POWER_PLANS
        
        controller = CpuController()
        result = controller.get_current_power_plan()
        
        assert result == "custom_plan"  # Should return the value as-is even if unknown
        mock_sub_process.run_cmd.assert_called_once()

    def test_determine_optimal_power_plan_hot(self, mock_process_utils):
        """Test determine_optimal_power_plan with hot temperature."""
        controller = CpuController()
        result = controller.determine_optimal_power_plan(43.0)  # Hot temperature
        
        assert result['powerplan'] == "powersave"
        assert result['sleep'] == 600
        mock_process_utils['get_process_list'].assert_not_called()

    def test_determine_optimal_power_plan_warm(self, mock_process_utils):
        """Test determine_optimal_power_plan with warm temperature."""
        controller = CpuController()
        result = controller.determine_optimal_power_plan(40.0)  # Warm temperature
        
        assert result['powerplan'] == "powersave"
        assert result['sleep'] == 300
        mock_process_utils['get_process_list'].assert_not_called()

    def test_determine_optimal_power_plan_none(self, mock_process_utils):
        """Test determine_optimal_power_plan with None temperature."""
        controller = CpuController()
        result = controller.determine_optimal_power_plan(None)
        
        assert result['powerplan'] == "powersave"
        assert result['sleep'] == 600
        mock_process_utils['get_process_list'].assert_not_called()

    def test_determine_optimal_power_plan_performance_app(self, mock_process_utils):
        """Test determine_optimal_power_plan with performance app."""
        mock_process_utils['detect_performance_apps'].return_value = True
        
        controller = CpuController()
        result = controller.determine_optimal_power_plan(35.0)  # Cool temperature
        
        assert result['powerplan'] == "performance"
        assert result['sleep'] == 60
        mock_process_utils['get_process_list'].assert_called_once()
        mock_process_utils['detect_performance_apps'].assert_called_once()

    def test_determine_optimal_power_plan_balance_app(self, mock_process_utils):
        """Test determine_optimal_power_plan with balance app."""
        mock_process_utils['detect_performance_apps'].return_value = False
        mock_process_utils['detect_balance_apps'].return_value = True
        
        controller = CpuController()
        result = controller.determine_optimal_power_plan(35.0)  # Cool temperature
        
        assert result['powerplan'] == "schedutil"
        assert result['sleep'] == 120
        mock_process_utils['get_process_list'].assert_called_once()
        mock_process_utils['detect_performance_apps'].assert_called_once()
        mock_process_utils['detect_balance_apps'].assert_called_once()

    def test_determine_optimal_power_plan_cool_default(self, mock_process_utils):
        """Test determine_optimal_power_plan with cool temperature and no special apps."""
        controller = CpuController()
        result = controller.determine_optimal_power_plan(35.0)  # Cool temperature
        
        assert result['powerplan'] == "powersave"
        assert result['sleep'] == 10
        mock_process_utils['get_process_list'].assert_called_once()

    def test_determine_optimal_power_plan_trend_rising(self, mock_process_utils):
        """Test determine_optimal_power_plan with rising temperature trend."""
        controller = CpuController()
        result = controller.determine_optimal_power_plan(35.0, trend="rising")
        
        # When trend is rising, sleep should be halved from default (10) with min 5s
        # So we expect sleep to be 5 (10 // 2 = 5)
        assert result['powerplan'] == "powersave"
        assert result['sleep'] == 5  # Sleep value is halved from 10 to 5 when trend is rising
        mock_process_utils['get_process_list'].assert_called_once()

    def test_determine_optimal_power_plan_trend_falling(self, mock_process_utils):
        """Test determine_optimal_power_plan with falling temperature trend."""
        controller = CpuController()
        result = controller.determine_optimal_power_plan(35.0, trend="falling")
        
        assert result['powerplan'] == "powersave"
        assert result['sleep'] == 20  # Should be doubled from default 10, max 300
        mock_process_utils['get_process_list'].assert_called_once()

    def test_determine_optimal_power_plan_stable_trend(self, mock_process_utils):
        """Test determine_optimal_power_plan with stable temperature trend."""
        controller = CpuController()
        result = controller.determine_optimal_power_plan(35.0, trend="stable")
        
        assert result['powerplan'] == "powersave"
        assert result['sleep'] == 10  # Should remain at default for stable trend
        mock_process_utils['get_process_list'].assert_called_once()

    def test_apply_optimal_power_plan(self):
        """Test apply_optimal_power_plan calls determine_optimal_power_plan and set_power_plan."""
        controller = CpuController()
        
        # Mock relevant methods
        controller.determine_optimal_power_plan = MagicMock(
            return_value={'powerplan': 'performance', 'sleep': 60}
        )
        controller.set_power_plan = MagicMock(return_value=True)
        
        # Call method
        result = controller.apply_optimal_power_plan(35.0, trend="rising")
        
        # Check behavior
        assert result is True
        controller.determine_optimal_power_plan.assert_called_once_with(35.0, trend="rising")
        controller.set_power_plan.assert_called_once_with('performance')

    def test_apply_settings_power_plan(self):
        """Test apply_settings with explicit power_plan setting."""
        controller = CpuController()
        controller.set_power_plan = MagicMock(return_value=True)
        
        result = controller.apply_settings({"power_plan": "performance"})
        
        assert result is True
        controller.set_power_plan.assert_called_once_with("performance")

    def test_apply_settings_invalid_power_plan_type(self):
        """Test apply_settings with invalid power_plan type."""
        controller = CpuController()
        controller.set_power_plan = MagicMock()
        
        result = controller.apply_settings({"power_plan": 123})  # Invalid type
        
        assert result is False
        controller.set_power_plan.assert_not_called()

    def test_apply_settings_auto_power_plan(self):
        """Test apply_settings with auto_power_plan."""
        controller = CpuController()
        controller.apply_optimal_power_plan = MagicMock(return_value=True)
        
        result = controller.apply_settings({
            "auto_power_plan": True,
            "temperature": 35.0
        })
        
        assert result is True
        controller.apply_optimal_power_plan.assert_called_once_with(35.0, trend=None)

    def test_apply_settings_auto_power_plan_with_trend(self):
        """Test apply_settings with auto_power_plan and trend."""
        controller = CpuController()
        controller.apply_optimal_power_plan = MagicMock(return_value=True)
        
        result = controller.apply_settings({
            "auto_power_plan": True,
            "temperature": 35.0,
            "trend": "rising"
        })
        
        assert result is True
        controller.apply_optimal_power_plan.assert_called_once_with(35.0, trend="rising")

    def test_apply_settings_auto_power_plan_no_temperature(self):
        """Test apply_settings with auto_power_plan but no temperature."""
        controller = CpuController()
        controller.apply_optimal_power_plan = MagicMock()
        
        result = controller.apply_settings({"auto_power_plan": True})
        
        assert result is False
        controller.apply_optimal_power_plan.assert_not_called()

    def test_apply_settings_auto_power_plan_invalid_trend(self):
        """Test apply_settings with auto_power_plan and invalid trend."""
        controller = CpuController()
        controller.apply_optimal_power_plan = MagicMock(return_value=True)
        
        result = controller.apply_settings({
            "auto_power_plan": True,
            "temperature": 35.0,
            "trend": "invalid"  # Invalid trend value
        })
        
        assert result is True  # Should still succeed but ignore the invalid trend
        controller.apply_optimal_power_plan.assert_called_once_with(35.0, trend=None)

    def test_apply_settings_auto_power_plan_invalid_trend_type(self):
        """Test apply_settings with auto_power_plan and invalid trend type."""
        controller = CpuController()
        controller.apply_optimal_power_plan = MagicMock(return_value=True)
        
        result = controller.apply_settings({
            "auto_power_plan": True,
            "temperature": 35.0,
            "trend": 123  # Invalid trend type
        })
        
        assert result is True  # Should still succeed but ignore the invalid trend
        controller.apply_optimal_power_plan.assert_called_once_with(35.0, trend=None)

    def test_apply_settings_unsupported(self):
        """Test apply_settings with unsupported settings."""
        controller = CpuController()
        
        result = controller.apply_settings({"unsupported_setting": "value"})
        
        assert result is False

    def test_apply_settings_multiple(self):
        """Test apply_settings with multiple settings."""
        controller = CpuController()
        controller.set_power_plan = MagicMock(return_value=True)
        
        result = controller.apply_settings({
            "power_plan": "performance",
            "unsupported_setting": "value"  # This should be ignored with warning
        })
        
        assert result is True  # Successful because power_plan was applied
        controller.set_power_plan.assert_called_once_with("performance")

    def test_apply_settings_with_empty_dict(self):
        """Test apply_settings with an empty dictionary."""
        controller = CpuController()
        result = controller.apply_settings({})
        
        assert result is False  # Should return False if no applicable settings

    def test_apply_settings_temperature_not_numeric(self):
        """Test apply_settings with auto_power_plan but non-numeric temperature."""
        controller = CpuController()
        controller.apply_optimal_power_plan = MagicMock()
        
        result = controller.apply_settings({
            "auto_power_plan": True,
            "temperature": "35.0"  # String instead of number
        })
        
        assert result is False  # Should return False for invalid temperature type
        controller.apply_optimal_power_plan.assert_not_called()

    def test_get_available_settings(self):
        """Test get_available_settings returns expected format."""
        controller = CpuController()
        controller.get_current_power_plan = MagicMock(return_value="performance")
        
        result = controller.get_available_settings()
        
        assert "power_plan" in result
        assert result["power_plan"] == "performance"
        assert "available_power_plans" in result
        assert result["available_power_plans"] == POWER_PLANS

    def test_get_available_settings_no_current_plan(self):
        """Test get_available_settings when current plan can't be read."""
        controller = CpuController()
        controller.get_current_power_plan = MagicMock(return_value=None)
        
        result = controller.get_available_settings()
        
        assert "power_plan" in result
        assert result["power_plan"] is None
        assert "available_power_plans" in result

    def test_cleanup(self):
        """Test cleanup runs without errors."""
        controller = CpuController()
        # Simply check that it doesn't raise exceptions
        controller.cleanup()

