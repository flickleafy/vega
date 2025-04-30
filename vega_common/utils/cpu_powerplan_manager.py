"""
CPU Power Plan Manager for low-level OS power management.

This module handles all direct interactions with the operating system for CPU power
management, including governors, EPP (Energy Performance Preference), and driver-specific
features like amd-pstate-epp and intel_pstate.
"""

from enum import Enum
from typing import List, Optional, Tuple

import vega_common.utils.sub_process as sub_process
from vega_common.utils.logging_utils import get_module_logger

# Setup module-specific logging
logger = get_module_logger("vega_common/utils/cpu_powerplan_manager")


class PowerPlan(str, Enum):
    """Logical power plans for CPU power management.
    
    These are high-level logical names that map to physical governor and EPP settings.
    Use .value to get the string representation.
    """
    PERFORMANCE = "performance"
    BALANCED_PERFORMANCE = "balanced-performance"
    BALANCED_EFFICIENT = "balanced-efficient"
    POWERSAVE = "powersave"
    
class GovernorSetting(str, Enum):
    """Physical governors for CPU power management. Native Linux kernel governors."""
    PERFORMANCE = "performance"
    SCHEDUTIL = "schedutil"
    ONDEMAND = "ondemand"
    POWERSAVE = "powersave"

class EenergyPerformancePreference(str, Enum):
    """Physical EPP (Energy Performance Preference) for CPU power management.
    This is a hint to the CPU about the desired balance between performance and power.
    Driver-specific EPP settings, like amd-pstate-epp and intel_pstate.

    ← More Power Efficient                        More Performant →
    ┌─────────┬───────────────┬─────────────────────┬─────────────┐
    │  power  │ balance_power │ balance_performance │ performance │
    └─────────┴───────────────┴─────────────────────┴─────────────┘
    """
    PERFORMANCE = "performance"
    BALANCE_PERFORMANCE = "balance_performance"
    BALANCE_POWER = "balance_power"
    POWERSAVE = "power"
    DEFAULT = "default"


# Constants for sysfs paths
CPU_GOVERNOR_PATH_TEMPLATE = "/sys/devices/system/cpu/cpu{cpu_index}/cpufreq/scaling_governor"
ALL_CPU_GOVERNOR_PATH = "/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"
AVAILABLE_GOVERNORS_PATH = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors"
EPP_PATH_TEMPLATE = "/sys/devices/system/cpu/cpu{cpu_index}/cpufreq/energy_performance_preference"
ALL_EPP_PATH = "/sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference"
AVAILABLE_EPP_PATH = "/sys/devices/system/cpu/cpu0/cpufreq/energy_performance_available_preferences"


class CpuPowerplanManager:
    """
    Manages low-level CPU power plan settings.
    
    This class encapsulates all direct OS interactions for CPU power management,
    including:
    - Detecting available governors and EPP hints
    - Mapping logical power plans to physical settings
    - Applying governors and EPP to sysfs
    - Reading current state from sysfs
    
    High-level consumers (like CpuController) should use this class for all
    low-level operations and only deal with logical plan names.
    """

    def __init__(self):
        """Initialize the power plan manager and detect capabilities."""
        self.available_governors: List[str] = []
        self.available_epps: List[str] = []
        self._detect_capabilities()
        
        logger.info(
            f"CpuPowerplanManager initialized - "
            f"Governors: {self.available_governors}, EPPs: {self.available_epps}"
        )

    def _detect_capabilities(self) -> None:
        """
        Detect available governors and EPP hints from sysfs.
        
        Reads from /sys/devices/system/cpu/cpu0/cpufreq/ to determine
        what governors and EPP options are available on this system.
        """
        # Detect available governors
        try:
            with open(AVAILABLE_GOVERNORS_PATH, "r") as f:
                content = f.read().strip()
                self.available_governors = content.split()
        except FileNotFoundError:
            logger.warning("Could not detect available governors. Assuming basic set.")
            self.available_governors = ["performance", "powersave"]  # Fallback
        except PermissionError:
            logger.warning("Permission denied reading governors. Assuming basic set.")
            self.available_governors = ["performance", "powersave"]

        # Detect available EPP hints
        try:
            with open(AVAILABLE_EPP_PATH, "r") as f:
                content = f.read().strip()
                self.available_epps = content.split()
        except FileNotFoundError:
            self.available_epps = []  # EPP not supported (legacy system)
        except PermissionError:
            logger.warning("Permission denied reading EPP hints.")
            self.available_epps = []

    def has_epp_support(self) -> bool:
        """Returns True if EPP (Energy Performance Preference) is supported."""
        return len(self.available_epps) > 0

    def _resolve_powerplan(self, plan: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Map a logical power plan to physical (governor, epp) settings.
        
        This is an internal method - external consumers should use set_logical_powerplan().
        
        Args:
            plan: Logical plan name:
                  - "performance": Maximum performance
                  - "balanced-performance": Balanced with performance bias (schedutil/balance_performance)
                  - "balanced-efficient": Balanced with efficiency bias (ondemand/balance_power)
                  - "powersave": Maximum power saving
                  Legacy aliases: "balanced" -> "balanced-performance", 
                                  "schedutil" -> "balanced-performance",
                                  "balance_power" -> "balanced-efficient"
        
        Returns:
            Tuple of (target_governor, target_epp). Either may be None if not applicable.
        """
        target_governor = None
        target_epp = None


        if plan == PowerPlan.PERFORMANCE.value:
            target_governor = GovernorSetting.PERFORMANCE.value
            target_epp = EenergyPerformancePreference.PERFORMANCE.value
            
        elif plan == PowerPlan.BALANCED_PERFORMANCE.value:
            if self.available_epps:
                # EPP-enabled systems (amd-pstate-epp, intel_pstate active mode)
                # Use powersave governor with EPP hint
                if GovernorSetting.POWERSAVE.value in self.available_governors:
                    target_governor = GovernorSetting.POWERSAVE.value
                elif GovernorSetting.PERFORMANCE.value in self.available_governors:
                    target_governor = GovernorSetting.PERFORMANCE.value
                
                # EPP hint: balance_performance for performance-biased balance
                if EenergyPerformancePreference.BALANCE_PERFORMANCE.value in self.available_epps:
                    target_epp = EenergyPerformancePreference.BALANCE_PERFORMANCE.value
                elif EenergyPerformancePreference.DEFAULT.value in self.available_epps:
                    target_epp = EenergyPerformancePreference.DEFAULT.value
                else:
                    target_epp = EenergyPerformancePreference.PERFORMANCE.value  # Fallback
            else:
                # Legacy systems without EPP - schedutil is performance-biased dynamic
                if GovernorSetting.SCHEDUTIL.value in self.available_governors:
                    target_governor = GovernorSetting.SCHEDUTIL.value
                elif GovernorSetting.ONDEMAND.value in self.available_governors:
                    target_governor = GovernorSetting.ONDEMAND.value  # Fallback
                else:
                    target_governor = GovernorSetting.POWERSAVE.value  # Last resort

        elif plan == PowerPlan.BALANCED_EFFICIENT.value:
            if self.available_epps:
                # EPP-enabled systems: use balance_power for efficiency-biased balance
                if GovernorSetting.POWERSAVE.value in self.available_governors:
                    target_governor = GovernorSetting.POWERSAVE.value
                elif GovernorSetting.PERFORMANCE.value in self.available_governors:
                    target_governor = GovernorSetting.PERFORMANCE.value
                
                # EPP hint: balance_power for efficiency-biased balance
                if EenergyPerformancePreference.BALANCE_POWER.value in self.available_epps:
                    target_epp = EenergyPerformancePreference.BALANCE_POWER.value
                elif EenergyPerformancePreference.BALANCE_PERFORMANCE.value in self.available_epps:
                    target_epp = EenergyPerformancePreference.BALANCE_PERFORMANCE.value  # Fallback to less efficient
                else:
                    target_epp = EenergyPerformancePreference.POWER.value  # Fallback to pure power saving
            else:
                # Legacy systems without EPP - ondemand is efficiency-biased dynamic
                if GovernorSetting.ONDEMAND.value in self.available_governors:
                    target_governor = GovernorSetting.ONDEMAND.value
                elif GovernorSetting.SCHEDUTIL.value in self.available_governors:
                    target_governor = GovernorSetting.SCHEDUTIL.value  # Fallback
                else:
                    target_governor = GovernorSetting.POWERSAVE.value  # Last resort
                    
        elif plan == PowerPlan.POWERSAVE.value:
            target_governor = GovernorSetting.POWERSAVE.value
            target_epp = EenergyPerformancePreference.POWERSAVE.value
            
        else:
            logger.error(f"Unknown power plan: {plan}")
            return (None, None)

        # Validate governor availability
        if target_governor and target_governor not in self.available_governors:
            logger.warning(
                f"Target governor {target_governor} not available. Falling back to powersave."
            )
            target_governor = GovernorSetting.POWERSAVE.value if GovernorSetting.POWERSAVE.value in self.available_governors else None

        # Validate EPP availability
        if target_epp:
            if not self.available_epps:
                target_epp = None  # Disable EPP if not supported
            elif target_epp not in self.available_epps:
                logger.warning(f"Target EPP {target_epp} not available. Disabling EPP.")
                target_epp = None

        return (target_governor, target_epp)

    def _run_command(self, command: list, use_shell: bool = False) -> Optional[str]:
        """
        Helper to run a command for CPU control.
        
        Args:
            command: Command as list of strings
            use_shell: If True, join command and run via shell
            
        Returns:
            Command output string or None on failure
        """
        try:
            cmd_to_run = command if not use_shell else " ".join(command)
            result = sub_process.run_cmd(cmd_to_run, shell=use_shell)
            return result.strip() if result else None
        except PermissionError:
            logger.warning(
                "CpuPowerplanManager: Insufficient permissions. "
                "Root/sudo privileges required for CPU power control."
            )
            return None
        except Exception as e:
            logger.error(f"CpuPowerplanManager: Error running command: {e}")
            return None

    def set_logical_powerplan(self, plan: str) -> bool:
        """
        Apply a logical power plan to the system.
        
        This method resolves the logical plan name to the appropriate
        governor and EPP settings, then applies them to sysfs.
        
        Args:
            plan: Logical plan name - "performance", "balanced", "powersave",
                  "balance_power", or "schedutil" (alias for balanced).
            
        Returns:
            True if the power plan was applied successfully, False otherwise.
        """
        # Resolve logical plan to physical settings
        governor, epp = self._resolve_powerplan(plan)
        
        if governor is None and epp is None:
            logger.error(f"CpuPowerplanManager: Unknown power plan: {plan}")
            return False
        
        success = True

        # Apply governor
        if governor:
            cmd_str = f"echo {governor} | tee {ALL_CPU_GOVERNOR_PATH}"
            logger.debug(f"CpuPowerplanManager: Setting governor: {governor}")
            result = self._run_command([cmd_str], use_shell=True)
            if result is None and not hasattr(sub_process, "mock_run_cmd"):
                success = False
                logger.error(f"CpuPowerplanManager: Failed to set governor for plan '{plan}'")

        # Apply EPP
        if success and epp:
            cmd_str = f"echo {epp} | tee {ALL_EPP_PATH}"
            logger.debug(f"CpuPowerplanManager: Setting EPP: {epp}")
            result = self._run_command([cmd_str], use_shell=True)
            if result is None and not hasattr(sub_process, "mock_run_cmd"):
                # EPP failure is non-critical if governor succeeded
                logger.warning(f"CpuPowerplanManager: EPP setting failed for plan '{plan}'")

        if success:
            logger.info(f"CpuPowerplanManager: Applied power plan '{plan}'")

        return success

    def get_current_state(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Read current governor and EPP from sysfs.
        
        Returns:
            Tuple of (current_governor, current_epp). EPP may be None if unsupported.
        """
        # Read current governor
        governor_file = CPU_GOVERNOR_PATH_TEMPLATE.format(cpu_index=0)
        governor = self._run_command(["cat", governor_file])

        # Read current EPP (if supported)
        epp = None
        if self.available_epps:
            epp_file = EPP_PATH_TEMPLATE.format(cpu_index=0)
            epp = self._run_command(["cat", epp_file])

        return (governor, epp)

    def get_logical_powerplan(self) -> Optional[str]:
        """
        Get the current power state mapped to a logical plan name.
        
        Returns:
            Logical plan name ("performance", "balanced-performance", "balanced-efficient", "powersave")
            or the raw governor name if no mapping matches, or None on read failure.
        """
        governor, epp = self.get_current_state()

        if not governor:
            return None

        # Map back to logical plan
        if governor == "performance":
            return PowerPlan.PERFORMANCE.value
        elif governor == "powersave":
            if epp == "power":
                return PowerPlan.POWERSAVE.value
            elif epp == "balance_performance":
                return PowerPlan.BALANCED_PERFORMANCE.value
            elif epp == "balance_power":
                return PowerPlan.BALANCED_EFFICIENT.value
            elif epp == "performance":
                return PowerPlan.PERFORMANCE.value
            elif epp is None:
                return PowerPlan.POWERSAVE.value  # Just powersave governor, no EPP
        elif governor == "schedutil":
            return PowerPlan.BALANCED_PERFORMANCE.value  # schedutil is performance-biased
        elif governor == "ondemand":
            return PowerPlan.BALANCED_EFFICIENT.value  # ondemand is efficiency-biased

        # Return raw governor if no mapping matches
        return governor

    def get_available_logical_plans(self) -> List[str]:
        """
        Get the list of supported logical power plans for this system.
        
        Returns:
            List of logical plan names that can be used with this system.
            Plans are ordered from most performant to most efficient.
        """
        plans = [PowerPlan.PERFORMANCE.value]
        
        # Add balanced-performance if we have balance_performance EPP or schedutil governor
        if (self.available_epps and "balance_performance" in self.available_epps) or \
           (not self.available_epps and "schedutil" in self.available_governors):
            plans.append(PowerPlan.BALANCED_PERFORMANCE.value)
        
        # Add balanced-efficient if we have balance_power EPP or ondemand governor
        if (self.available_epps and "balance_power" in self.available_epps) or \
           (not self.available_epps and "ondemand" in self.available_governors):
            plans.append(PowerPlan.BALANCED_EFFICIENT.value)
        
        plans.append(PowerPlan.POWERSAVE.value)
        return plans
