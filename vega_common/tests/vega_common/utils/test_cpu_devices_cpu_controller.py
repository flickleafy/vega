import sys
import os
import io
import logging
import tempfile
from typing import Dict, List, Any, Optional

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

# Import CpuController from cpu_devices
from vega_common.utils.cpu_devices import CpuController
from vega_common.utils.device_status import DeviceStatus

# Define the list of power plans used in the tests (matches LOGICAL_POWER_PLANS)
LOGICAL_POWER_PLANS = ["performance", "balanced-performance", "balanced-efficient", "powersave"]


@pytest.fixture
def mock_powerplan_manager():
    """Create a mock for CpuPowerplanManager."""
    with patch("vega_common.utils.cpu_devices.CpuPowerplanManager") as mock_class:
        mock_instance = MagicMock()
        mock_instance.available_governors = ["performance", "powersave", "schedutil"]
        mock_instance.available_epps = ["performance", "balance_performance", "power"]
        mock_instance.set_logical_powerplan.return_value = True
        mock_instance.get_logical_powerplan.return_value = "performance"
        mock_instance.get_available_logical_plans.return_value = ["performance", "balanced-performance", "balanced-efficient", "powersave"]
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_sub_process():
    """Create a mock for subprocess operations."""
    with patch("vega_common.utils.cpu_powerplan_manager.sub_process") as mock:
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
                    "get_process_list": proc_mock,
                }
                perf_mock.return_value = False
                bal_mock.return_value = False
                yield mocks


class TestCpuController:
    """Tests for the CpuController class."""

    def test_init_default(self, mock_powerplan_manager):
        """Test initialization with default device ID."""
        controller = CpuController()
        assert controller.device_id == "cpu_main"
        assert controller.device_type == "cpu"

    def test_init_custom(self, mock_powerplan_manager):
        """Test initialization with custom device ID."""
        controller = CpuController(device_id="custom_cpu")
        assert controller.device_id == "custom_cpu"
        assert controller.device_type == "cpu"

    def test_set_power_plan_valid(self, mock_powerplan_manager):
        """Test set_power_plan with a valid plan."""
        mock_powerplan_manager.set_logical_powerplan.return_value = True

        controller = CpuController()
        result = controller.set_power_plan("performance")

        assert result is True
        mock_powerplan_manager.set_logical_powerplan.assert_called_once_with("performance")

    def test_set_power_plan_invalid(self, mock_powerplan_manager):
        """Test set_power_plan with an invalid plan."""
        mock_powerplan_manager.set_logical_powerplan.return_value = False
        
        controller = CpuController()
        result = controller.set_power_plan("invalid_plan")

        assert result is False
        mock_powerplan_manager.set_logical_powerplan.assert_called_once_with("invalid_plan")

    def test_set_power_plan_command_failed(self, mock_powerplan_manager):
        """Test set_power_plan when command execution fails."""
        mock_powerplan_manager.set_logical_powerplan.return_value = False

        controller = CpuController()
        result = controller.set_power_plan("performance")

        assert result is False
        mock_powerplan_manager.set_logical_powerplan.assert_called_once()

    def test_get_current_power_plan_success(self, mock_powerplan_manager):
        """Test get_current_power_plan with successful execution."""
        mock_powerplan_manager.get_logical_powerplan.return_value = "performance"

        controller = CpuController()
        result = controller.get_current_power_plan()

        assert result == "performance"
        mock_powerplan_manager.get_logical_powerplan.assert_called_once()

    def test_get_current_power_plan_failure(self, mock_powerplan_manager):
        """Test get_current_power_plan when read fails."""
        mock_powerplan_manager.get_logical_powerplan.return_value = None

        controller = CpuController()
        result = controller.get_current_power_plan()

        assert result is None
        mock_powerplan_manager.get_logical_powerplan.assert_called_once()

    def test_get_current_power_plan_unknown(self, mock_powerplan_manager):
        """Test get_current_power_plan returns unknown plan."""
        mock_powerplan_manager.get_logical_powerplan.return_value = "unknown_plan"

        controller = CpuController()
        result = controller.get_current_power_plan()

        assert result == "unknown_plan"
        mock_powerplan_manager.get_logical_powerplan.assert_called_once()

    def test_determine_optimal_power_plan_hot(self, mock_process_utils, mock_powerplan_manager):
        """Test determine_optimal_power_plan with hot temperature."""
        controller = CpuController()
        # Hot threshold is tjmax * 0.75 (e.g., 71.25°C for 95°C tjmax)
        # Using 80°C to be safely above the hot threshold
        result = controller.determine_optimal_power_plan(80.0)  # Hot temperature

        assert result["powerplan"] == "powersave"
        assert result["sleep"] == 600
        mock_process_utils["get_process_list"].assert_not_called()

    def test_determine_optimal_power_plan_warm(self, mock_process_utils, mock_powerplan_manager):
        """Test determine_optimal_power_plan with warm temperature."""
        controller = CpuController()
        # Warm threshold is tjmax * 0.70 (e.g., 66.5°C for 95°C tjmax)
        # Using 68°C to be above warm but below hot threshold
        result = controller.determine_optimal_power_plan(68.0)  # Warm temperature

        assert result["powerplan"] == "balanced-efficient"
        assert result["sleep"] == 300
        mock_process_utils["get_process_list"].assert_not_called()

    def test_determine_optimal_power_plan_none(self, mock_process_utils, mock_powerplan_manager):
        """Test determine_optimal_power_plan with None temperature."""
        controller = CpuController()
        result = controller.determine_optimal_power_plan(None)

        assert result["powerplan"] == "powersave"
        assert result["sleep"] == 600
        mock_process_utils["get_process_list"].assert_not_called()

    def test_determine_optimal_power_plan_performance_app(self, mock_process_utils, mock_powerplan_manager):
        """Test determine_optimal_power_plan with performance app."""
        mock_process_utils["detect_performance_apps"].return_value = True

        controller = CpuController()
        result = controller.determine_optimal_power_plan(35.0)  # Cool temperature

        assert result["powerplan"] == "performance"
        assert result["sleep"] == 60
        mock_process_utils["get_process_list"].assert_called_once()
        mock_process_utils["detect_performance_apps"].assert_called_once()

    def test_determine_optimal_power_plan_balance_app(self, mock_process_utils, mock_powerplan_manager):
        """Test determine_optimal_power_plan with balance app."""
        mock_process_utils["detect_performance_apps"].return_value = False
        mock_process_utils["detect_balance_apps"].return_value = True

        controller = CpuController()
        result = controller.determine_optimal_power_plan(35.0)  # Cool temperature

        assert result["powerplan"] == "balanced-efficient"
        assert result["sleep"] == 120
        mock_process_utils["get_process_list"].assert_called_once()
        mock_process_utils["detect_performance_apps"].assert_called_once()
        mock_process_utils["detect_balance_apps"].assert_called_once()

    def test_determine_optimal_power_plan_cool_default(self, mock_process_utils, mock_powerplan_manager):
        """Test determine_optimal_power_plan with cool temperature and no special apps."""
        controller = CpuController()
        result = controller.determine_optimal_power_plan(35.0)  # Cool temperature

        assert result["powerplan"] == "powersave"
        assert result["sleep"] == 10
        mock_process_utils["get_process_list"].assert_called_once()

    def test_determine_optimal_power_plan_trend_rising(self, mock_process_utils, mock_powerplan_manager):
        """Test determine_optimal_power_plan with rising temperature trend."""
        controller = CpuController()
        result = controller.determine_optimal_power_plan(35.0, trend="rising")

        # When trend is rising, sleep should be halved from default (10) with min 5s
        # So we expect sleep to be 5 (10 // 2 = 5)
        assert result["powerplan"] == "powersave"
        assert result["sleep"] == 5  # Sleep value is halved from 10 to 5 when trend is rising
        mock_process_utils["get_process_list"].assert_called_once()

    def test_determine_optimal_power_plan_trend_falling(self, mock_process_utils, mock_powerplan_manager):
        """Test determine_optimal_power_plan with falling temperature trend."""
        controller = CpuController()
        result = controller.determine_optimal_power_plan(35.0, trend="falling")

        assert result["powerplan"] == "powersave"
        assert result["sleep"] == 20  # Should be doubled from default 10, max 300
        mock_process_utils["get_process_list"].assert_called_once()

    def test_determine_optimal_power_plan_stable_trend(self, mock_process_utils, mock_powerplan_manager):
        """Test determine_optimal_power_plan with stable temperature trend."""
        controller = CpuController()
        result = controller.determine_optimal_power_plan(35.0, trend="stable")

        assert result["powerplan"] == "powersave"
        assert result["sleep"] == 10  # Should remain at default for stable trend
        mock_process_utils["get_process_list"].assert_called_once()

    def test_apply_optimal_power_plan(self, mock_powerplan_manager):
        """Test apply_optimal_power_plan calls determine_optimal_power_plan and set_power_plan."""
        controller = CpuController()

        # Mock relevant methods
        controller.determine_optimal_power_plan = MagicMock(
            return_value={"powerplan": "performance", "sleep": 60}
        )
        controller.set_power_plan = MagicMock(return_value=True)

        # Call method
        result = controller.apply_optimal_power_plan(35.0, trend="rising")

        # Check behavior
        assert result is True
        controller.determine_optimal_power_plan.assert_called_once_with(35.0, trend="rising")
        controller.set_power_plan.assert_called_once_with("performance")

    def test_apply_settings_power_plan(self, mock_powerplan_manager):
        """Test apply_settings with explicit power_plan setting."""
        controller = CpuController()
        controller.set_power_plan = MagicMock(return_value=True)

        result = controller.apply_settings({"power_plan": "performance"})

        assert result is True
        controller.set_power_plan.assert_called_once_with("performance")

    def test_apply_settings_invalid_power_plan_type(self, mock_powerplan_manager):
        """Test apply_settings with invalid power_plan type."""
        controller = CpuController()
        controller.set_power_plan = MagicMock()

        result = controller.apply_settings({"power_plan": 123})  # Invalid type

        assert result is False
        controller.set_power_plan.assert_not_called()

    def test_apply_settings_auto_power_plan(self, mock_powerplan_manager):
        """Test apply_settings with auto_power_plan."""
        controller = CpuController()
        controller.apply_optimal_power_plan = MagicMock(return_value=True)

        result = controller.apply_settings({"auto_power_plan": True, "temperature": 35.0})

        assert result is True
        controller.apply_optimal_power_plan.assert_called_once_with(35.0, trend=None)

    def test_apply_settings_auto_power_plan_with_trend(self, mock_powerplan_manager):
        """Test apply_settings with auto_power_plan and trend."""
        controller = CpuController()
        controller.apply_optimal_power_plan = MagicMock(return_value=True)

        result = controller.apply_settings(
            {"auto_power_plan": True, "temperature": 35.0, "trend": "rising"}
        )

        assert result is True
        controller.apply_optimal_power_plan.assert_called_once_with(35.0, trend="rising")

    def test_apply_settings_auto_power_plan_no_temperature(self, mock_powerplan_manager):
        """Test apply_settings with auto_power_plan but no temperature."""
        controller = CpuController()
        controller.apply_optimal_power_plan = MagicMock()

        result = controller.apply_settings({"auto_power_plan": True})

        assert result is False
        controller.apply_optimal_power_plan.assert_not_called()

    def test_apply_settings_auto_power_plan_invalid_trend(self, mock_powerplan_manager):
        """Test apply_settings with auto_power_plan and invalid trend."""
        controller = CpuController()
        controller.apply_optimal_power_plan = MagicMock(return_value=True)

        result = controller.apply_settings(
            {
                "auto_power_plan": True,
                "temperature": 35.0,
                "trend": "invalid",  # Invalid trend value
            }
        )

        assert result is True  # Should still succeed but ignore the invalid trend
        controller.apply_optimal_power_plan.assert_called_once_with(35.0, trend=None)

    def test_apply_settings_auto_power_plan_invalid_trend_type(self, mock_powerplan_manager):
        """Test apply_settings with auto_power_plan and invalid trend type."""
        controller = CpuController()
        controller.apply_optimal_power_plan = MagicMock(return_value=True)

        result = controller.apply_settings(
            {"auto_power_plan": True, "temperature": 35.0, "trend": 123}  # Invalid trend type
        )

        assert result is True  # Should still succeed but ignore the invalid trend
        controller.apply_optimal_power_plan.assert_called_once_with(35.0, trend=None)

    def test_apply_settings_unsupported(self, mock_powerplan_manager):
        """Test apply_settings with unsupported settings."""
        controller = CpuController()

        result = controller.apply_settings({"unsupported_setting": "value"})

        assert result is False

    def test_apply_settings_multiple(self, mock_powerplan_manager):
        """Test apply_settings with multiple settings."""
        controller = CpuController()
        controller.set_power_plan = MagicMock(return_value=True)

        result = controller.apply_settings(
            {
                "power_plan": "performance",
                "unsupported_setting": "value",  # This should be ignored with warning
            }
        )

        assert result is True  # Successful because power_plan was applied
        controller.set_power_plan.assert_called_once_with("performance")

    def test_apply_settings_with_empty_dict(self, mock_powerplan_manager):
        """Test apply_settings with an empty dictionary."""
        controller = CpuController()
        result = controller.apply_settings({})

        assert result is False  # Should return False if no applicable settings

    def test_apply_settings_temperature_not_numeric(self, mock_powerplan_manager):
        """Test apply_settings with auto_power_plan but non-numeric temperature."""
        controller = CpuController()
        controller.apply_optimal_power_plan = MagicMock()

        result = controller.apply_settings(
            {"auto_power_plan": True, "temperature": "35.0"}  # String instead of number
        )

        assert result is False  # Should return False for invalid temperature type
        controller.apply_optimal_power_plan.assert_not_called()

    def test_get_available_settings(self, mock_powerplan_manager):
        """Test get_available_settings returns expected format."""
        mock_powerplan_manager.get_logical_powerplan.return_value = "performance"
        mock_powerplan_manager.get_available_logical_plans.return_value = LOGICAL_POWER_PLANS
        
        controller = CpuController()
        result = controller.get_available_settings()

        assert "power_plan" in result
        assert result["power_plan"] == "performance"
        assert "available_power_plans" in result
        assert result["available_power_plans"] == LOGICAL_POWER_PLANS

    def test_get_available_settings_no_current_plan(self, mock_powerplan_manager):
        """Test get_available_settings when current plan can't be read."""
        mock_powerplan_manager.get_logical_powerplan.return_value = None
        
        controller = CpuController()
        result = controller.get_available_settings()

        assert "power_plan" in result
        assert result["power_plan"] is None
        assert "available_power_plans" in result

    def test_cleanup(self, mock_powerplan_manager):
        """Test cleanup runs without errors."""
        controller = CpuController()
        # Simply check that it doesn't raise exceptions
        controller.cleanup()
