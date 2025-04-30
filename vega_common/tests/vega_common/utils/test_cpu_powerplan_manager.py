"""
Tests for the CpuPowerplanManager class.
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open


class TestCpuPowerplanManager:
    """Tests for the CpuPowerplanManager class."""

    @pytest.fixture
    def mock_governors_file(self):
        """Mock available governors sysfs file."""
        return "performance powersave schedutil ondemand"

    @pytest.fixture
    def mock_epp_file(self):
        """Mock available EPP hints sysfs file."""
        return "default performance balance_performance balance_power power"

    @pytest.fixture
    def mock_sub_process(self):
        """Create a mock for subprocess operations."""
        with patch("vega_common.utils.cpu_powerplan_manager.sub_process") as mock:
            mock.run_cmd = MagicMock(return_value="success")
            yield mock

    def test_init_with_epp_support(self, mock_governors_file, mock_epp_file):
        """Test initialization on a system with EPP support."""
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                mock_open(read_data=mock_epp_file)(),
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        assert "performance" in manager.available_governors
        assert "powersave" in manager.available_governors
        assert "balance_performance" in manager.available_epps
        assert manager.has_epp_support() is True

    def test_init_without_epp_support(self, mock_governors_file):
        """Test initialization on a legacy system without EPP."""
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                FileNotFoundError(),  # EPP file doesn't exist
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        assert "performance" in manager.available_governors
        assert manager.available_epps == []
        assert manager.has_epp_support() is False

    def test_init_fallback_when_sysfs_not_found(self):
        """Test initialization fallback when sysfs files not found."""
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [FileNotFoundError(), FileNotFoundError()]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        assert manager.available_governors == ["performance", "powersave"]
        assert manager.available_epps == []

    def test_resolve_powerplan_performance(self, mock_governors_file, mock_epp_file):
        """Test resolving performance plan."""
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                mock_open(read_data=mock_epp_file)(),
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        governor, epp = manager._resolve_powerplan("performance")
        assert governor == "performance"
        assert epp == "performance"

    def test_resolve_powerplan_balanced_performance_with_epp(self, mock_governors_file, mock_epp_file):
        """Test resolving balanced-performance plan on EPP-enabled system."""
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                mock_open(read_data=mock_epp_file)(),
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        governor, epp = manager._resolve_powerplan("balanced-performance")
        assert governor == "powersave"  # Uses powersave governor with EPP
        assert epp == "balance_performance"

    def test_resolve_powerplan_balanced_performance_legacy(self, mock_governors_file):
        """Test resolving balanced-performance plan on legacy system."""
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                FileNotFoundError(),  # No EPP
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        governor, epp = manager._resolve_powerplan("balanced-performance")
        assert governor == "schedutil"  # Uses schedutil on legacy
        assert epp is None

    def test_resolve_powerplan_balanced_performance_with_epp(self, mock_governors_file, mock_epp_file):
        """Test that balanced-performance resolves correctly on EPP-enabled system."""
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                mock_open(read_data=mock_epp_file)(),
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        governor, epp = manager._resolve_powerplan("balanced-performance")
        assert governor == "powersave"  # Uses powersave governor with EPP hint
        assert epp == "balance_performance"


    def test_resolve_powerplan_balanced_efficient_with_epp(self, mock_governors_file, mock_epp_file):
        """Test resolving balanced-efficient plan on EPP-enabled system."""
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                mock_open(read_data=mock_epp_file)(),
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        governor, epp = manager._resolve_powerplan("balanced-efficient")
        assert governor == "powersave"  # Uses powersave governor with EPP
        assert epp == "balance_power"

    def test_resolve_powerplan_powersave(self, mock_governors_file, mock_epp_file):
        """Test resolving powersave plan."""
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                mock_open(read_data=mock_epp_file)(),
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        governor, epp = manager._resolve_powerplan("powersave")
        assert governor == "powersave"
        assert epp == "power"  # Uses 'power' EPP hint for maximum power savings

    def test_resolve_powerplan_unknown(self, mock_governors_file, mock_epp_file):
        """Test resolving unknown plan returns None."""
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                mock_open(read_data=mock_epp_file)(),
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        governor, epp = manager._resolve_powerplan("unknown_plan")
        assert governor is None
        assert epp is None

    def test_set_logical_powerplan_success(self, mock_governors_file, mock_epp_file, mock_sub_process):
        """Test setting logical powerplan successfully."""
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                mock_open(read_data=mock_epp_file)(),
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        result = manager.set_logical_powerplan("performance")
        
        assert result is True
        assert mock_sub_process.run_cmd.call_count == 2  # Governor + EPP

    def test_set_logical_powerplan_balanced_performance(self, mock_governors_file, mock_epp_file, mock_sub_process):
        """Test setting balanced-performance powerplan."""
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                mock_open(read_data=mock_epp_file)(),
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        result = manager.set_logical_powerplan("balanced-performance")
        
        assert result is True
        assert mock_sub_process.run_cmd.call_count == 2  # Governor + EPP

    def test_set_logical_powerplan_unknown(self, mock_governors_file, mock_epp_file, mock_sub_process):
        """Test setting unknown powerplan returns False."""
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                mock_open(read_data=mock_epp_file)(),
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        result = manager.set_logical_powerplan("unknown_plan")
        
        assert result is False
        mock_sub_process.run_cmd.assert_not_called()

    def test_get_current_state(self, mock_governors_file, mock_epp_file, mock_sub_process):
        """Test reading current state."""
        mock_sub_process.run_cmd.side_effect = ["powersave", "balance_performance"]
        
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                mock_open(read_data=mock_epp_file)(),
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        governor, epp = manager.get_current_state()
        
        assert governor == "powersave"
        assert epp == "balance_performance"

    def test_get_logical_powerplan_balanced_performance(self, mock_governors_file, mock_epp_file, mock_sub_process):
        """Test getting logical plan for balanced-performance state."""
        mock_sub_process.run_cmd.side_effect = ["powersave", "balance_performance"]
        
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                mock_open(read_data=mock_epp_file)(),
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        plan = manager.get_logical_powerplan()
        assert plan == "balanced-performance"

    def test_get_logical_powerplan_performance(self, mock_governors_file, mock_epp_file, mock_sub_process):
        """Test getting logical plan for performance state."""
        mock_sub_process.run_cmd.side_effect = ["performance", "performance"]
        
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                mock_open(read_data=mock_epp_file)(),
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        plan = manager.get_logical_powerplan()
        assert plan == "performance"

    def test_get_logical_powerplan_schedutil(self, mock_governors_file, mock_sub_process):
        """Test getting logical plan for schedutil governor (legacy)."""
        mock_sub_process.run_cmd.return_value = "schedutil"
        
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                FileNotFoundError(),  # No EPP
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        plan = manager.get_logical_powerplan()
        assert plan == "balanced-performance"  # schedutil maps to balanced-performance

    def test_get_logical_powerplan_ondemand(self, mock_governors_file, mock_sub_process):
        """Test getting logical plan for ondemand governor (legacy)."""
        mock_sub_process.run_cmd.return_value = "ondemand"
        
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                FileNotFoundError(),  # No EPP
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        plan = manager.get_logical_powerplan()
        assert plan == "balanced-efficient"  # ondemand maps to balanced-efficient

    def test_get_available_logical_plans_with_epp(self, mock_governors_file, mock_epp_file):
        """Test available logical plans on EPP system with balance_power."""
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                mock_open(read_data=mock_epp_file)(),
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        plans = manager.get_available_logical_plans()
        assert "performance" in plans
        assert "balanced-performance" in plans
        assert "balanced-efficient" in plans
        assert "powersave" in plans

    def test_get_available_logical_plans_legacy_with_ondemand(self, mock_governors_file):
        """Test available logical plans on legacy system with ondemand."""
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data=mock_governors_file)(),
                FileNotFoundError(),  # No EPP
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        plans = manager.get_available_logical_plans()
        assert "performance" in plans
        assert "balanced-performance" in plans
        assert "balanced-efficient" in plans  # Available because ondemand is in governors
        assert "powersave" in plans

    def test_get_available_logical_plans_legacy_no_ondemand(self):
        """Test available logical plans on legacy system without ondemand."""
        with patch("builtins.open", mock_open()) as m:
            m.side_effect = [
                mock_open(read_data="performance powersave schedutil")(),
                FileNotFoundError(),  # No EPP
            ]
            from vega_common.utils.cpu_powerplan_manager import CpuPowerplanManager
            manager = CpuPowerplanManager()

        plans = manager.get_available_logical_plans()
        assert "performance" in plans
        assert "balanced-performance" in plans
        assert "balanced-efficient" not in plans  # Not available without ondemand or EPP
        assert "powersave" in plans
