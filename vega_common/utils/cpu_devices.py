"""
Concrete implementation for monitoring CPU metrics using psutil.
"""

import logging
import sys
from typing import List, Optional, Dict, Any, Union

# Import psutil conditionally based on platform
try:
    # psutil.sensors_temperatures() is only available on Linux and FreeBSD
    if sys.platform.startswith('linux') or sys.platform.startswith('freebsd'):
        import psutil
    else:
        psutil = None
except ImportError:
    psutil = None
    # Log error only if psutil is expected but not found
    if sys.platform.startswith('linux') or sys.platform.startswith('freebsd'):
        logging.error("psutil library not found, but required for CPU monitoring on this platform.")
    else:
        logging.info("psutil library not found or not supported on this platform. CPU monitoring disabled.")

from .device_monitor import DeviceMonitor
from .device_status import DeviceStatus
import vega_common.utils.sub_process as sub_process
from .device_controller import DeviceController
# Import process utilities
from vega_common.utils.process_utils import (
    get_process_list,
    detect_balance_apps,
    detect_performance_apps
)

# Default sensor names to look for CPU temperature, ordered by likely preference
DEFAULT_CPU_TEMP_SENSOR_LABELS = (
    # AMD Ryzen specific (most reliable first)
    'tdie',          # Average die temperature
    'tctl',          # Control temperature (may have offset)
    'tccd1',         # CCD1 temperature
    'tccd2',         # CCD2 temperature (if present)
    # Intel specific (most reliable first)
    'package_id_0',  # Package temperature (often ID 0, normalized)
    'package',   # Intel package temperature (often Package id 0)
    'core_0',        # Core 0 temperature (normalized)
    'core_1',        # Core 1 temperature (normalized)
    # Generic / Common labels (normalized)
    'cpu_temperature', # Often used by generic drivers
    'processor_temperature', # Another common generic label
    'cpu_temp',      # Abbreviated generic label
    'core_temp',     # Generic core temp label
    'temp1',         # Common generic sensor label (often CPU)
    'temp2',         # Another generic sensor label
    # Platform/Device specific (normalized)
    'cpu',           # Sometimes used by thinkpad_acpi or others
    'cpu_die',       # Sometimes used by applesmc
    # Less common but possible Intel labels (normalized)
    'physical_id_0', # Another way package temp might be labelled
    # Add other known specific labels if targeting particular hardware
    # Ensure labels are lowercased and spaces replaced with underscores
    # for matching against normalized labels in the update_status method.
)
# Default device names to look for CPU temperature sensors, ordered by likely relevance
DEFAULT_CPU_TEMP_DEVICE_NAMES = (
    'k10temp',       # Common for AMD CPUs (older and Ryzen)
    'coretemp',      # Common for Intel CPUs
    'zenpower',      # Alternative/newer AMD Ryzen driver
    'cpu_thermal',   # Generic thermal zone often linked to CPU
    'acpitz',        # ACPI thermal zones, can include CPU
    'platform',      # Platform-specific sensors (e.g., some Intel chipsets)
    'thinkpad',      # Lenovo ThinkPad specific ACPI sensors
    'applesmc',      # Apple System Management Controller sensors
    'nct6775',       # Nuvoton sensor chip (common on motherboards)
    'nct6791',       # Nuvoton sensor chip
    'it87',          # ITE sensor chip (common on motherboards)
    # Add other specific chip names if known for target hardware, e.g., it86*, nct679*
)

# Constants for power plans (CPU governors)
POWER_PLANS = ["powersave", "schedutil", "performance"]
CPU_GOVERNOR_PATH_TEMPLATE = "/sys/devices/system/cpu/cpu{cpu_index}/cpufreq/scaling_governor"
ALL_CPU_GOVERNOR_PATH = "/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor" # For setting all cores


class CpuController(DeviceController):
    """Controller for CPU properties like power plan (governor)."""

    def __init__(self, device_id: str = "cpu_main"):
        """Initialize the CPU controller."""
        # O(1) complexity
        super().__init__(device_id=device_id, device_type="cpu", device_name="CPU") # Added device_name
        logging.info(f"Initialized controller for CPU (ID: {self.device_id})")
        # No complex initialization needed like NVML

    def _run_cpu_command(self, command: list[str], use_shell: bool = False) -> Optional[str]:
        """Helper to run a command related to CPU control."""
        # Complexity depends on sub_process.run_cmd, likely O(P) where P is process execution time
        try:
            cmd_to_run = command if not use_shell else " ".join(command)
            # Assuming run_cmd accepts use_shell argument
            result = sub_process.run_cmd(cmd_to_run, use_shell=use_shell) 
            return result.strip() if result else None
        except Exception as e:
            logging.error(f"CPU Controller ({self.device_id}): Error running command '{cmd_to_run}': {e}", exc_info=True)
            return None

    def set_power_plan(self, plan: str) -> bool:
        """Sets the CPU scaling governor for all cores."""
        # O(P) complexity due to command execution (set + verify)
        if plan not in POWER_PLANS:
            logging.error(f"CPU Controller ({self.device_id}): Invalid power plan '{plan}'. Must be one of {POWER_PLANS}.")
            return False

        # Construct the command using tee. This often requires root privileges.
        # Assuming sub_process.run_cmd handles permissions (e.g., runs as root or uses sudo internally).
        cmd_str = f"echo {plan} | tee {ALL_CPU_GOVERNOR_PATH}"
        
        logging.debug(f"CPU Controller ({self.device_id}): Running command: {cmd_str}")
        # Use use_shell=True because of the pipe '|'
        result = self._run_cpu_command([cmd_str], use_shell=True) 

        # Check if command execution itself failed
        if result is None and not hasattr(sub_process, 'mock_run_cmd'): # Modified to use hasattr for safer check
             # If result is None and it wasn't due to a test side effect raising an exception,
             # it means _run_cpu_command caught an exception.
             logging.error(f"CPU Controller ({self.device_id}): Failed to execute command to set power plan to '{plan}'.")
             return False
             
        # Verify by reading back the governor of the first core
        # Small delay might sometimes be needed for the change to reflect, but usually not for governors.
        # time.sleep(0.1) 
        current_plan = self.get_current_power_plan()
        if current_plan == plan:
            logging.info(f"CPU Controller ({self.device_id}): Successfully set power plan to '{plan}'.")
            return True
        else:
            logging.warning(f"CPU Controller ({self.device_id}): Set power plan command ran, but current plan is '{current_plan}' (expected '{plan}'). Verification failed.")
            return False

    def get_current_power_plan(self) -> Optional[str]:
        """Gets the current CPU scaling governor for core 0."""
        # O(P) complexity due to command execution
        governor_file = CPU_GOVERNOR_PATH_TEMPLATE.format(cpu_index=0)
        cmd = ["cat", governor_file]
        result = self._run_cpu_command(cmd)
        
        if result is not None:
            # Check if the result is one of the known plans
             if result not in POWER_PLANS:
                 logging.warning(f"CPU Controller ({self.device_id}): Read unknown power plan '{result}' from {governor_file}.")
             return result # Return the value read, known or unknown
        else:
             # Error occurred during command execution
             logging.error(f"CPU Controller ({self.device_id}): Failed to read power plan from {governor_file}.")
             return None

    def determine_optimal_power_plan(self, temperature: Optional[float], trend: Optional[str] = None) -> Dict[str, Union[str, int]]:
        """Determines the optimal CPU power plan and recommended sleep interval.

        Args:
            temperature (Optional[float]): The relevant temperature reading.
            trend (Optional[str]): Temperature trend ("rising", "falling", "stable"). Defaults to None.

        Returns:
            Dict[str, Union[str, int]]: Dictionary with 'powerplan' (str) and 'sleep' (int) keys.

        Complexity: O(ProcList) + O(DetectApps) where ProcList is complexity of get_process_list and DetectApps is complexity of app detection functions.
        """
        # O(ProcList) - Complexity depends on psutil and filtering logic
        process_list = get_process_list()

        # Defaults
        powerplan = "powersave"
        sleep = 10 # Default sleep for idle/cool state

        # Handle unknown temperature
        if temperature is None:
            logging.debug(f"CPU Controller ({self.device_id}): Temperature is None, defaulting to powersave, sleep 600.")
            return {'powerplan': 'powersave', 'sleep': 600} # Long sleep if temp unknown

        # --- Temperature-based rules ---
        # O(1) comparisons
        is_hot = temperature > 42
        is_warm = temperature > 39

        if is_hot:
            logging.debug(f"CPU Controller ({self.device_id}): Temp ({temperature}°C) > 42°C (hot), suggesting powersave, sleep 600.")
            powerplan = "powersave"
            sleep = 600
        elif is_warm:
            logging.debug(f"CPU Controller ({self.device_id}): Temp ({temperature}°C) > 39°C (warm), suggesting powersave, sleep 300.")
            powerplan = "powersave"
            sleep = 300
        else:
             # --- Application-based rules (only if not warm/hot) ---
            # O(DetectApps)
            performance_app_detected = detect_performance_apps(process_list)
            balance_app_detected = detect_balance_apps(process_list)

            if performance_app_detected:
                logging.debug(f"CPU Controller ({self.device_id}): Performance app detected, suggesting performance, sleep 60.")
                powerplan = "performance"
                sleep = 60
            elif balance_app_detected:
                logging.debug(f"CPU Controller ({self.device_id}): Balance app detected, suggesting schedutil, sleep 120.")
                powerplan = "schedutil"
                sleep = 120
            else:
                # --- Trend influence (only if cool and no specific apps) ---
                # O(1) comparisons
                if trend == "rising":
                    # Become slightly more responsive if temp is rising from cool state
                    sleep = max(10, sleep // 2) # Halve sleep, min 10s
                    logging.debug(f"CPU Controller ({self.device_id}): Temp cool, trend rising. Shortening sleep to {sleep}s.")
                    # Optionally, could switch to schedutil sooner if rising fast, but keep simple for now
                    # powerplan = "schedutil"
                elif trend == "falling":
                    # Become less responsive if temp is falling from cool state
                    sleep = min(300, sleep * 2) # Double sleep, max 300s (warm threshold sleep)
                    logging.debug(f"CPU Controller ({self.device_id}): Temp cool, trend falling. Lengthening sleep to {sleep}s.")
                else: # Stable or None trend
                    logging.debug(f"CPU Controller ({self.device_id}): Temp cool, trend stable/None. Defaulting to powersave, sleep {sleep}.")
                    # Keep default powersave, sleep 10

        logging.info(f"CPU Controller ({self.device_id}): Determined plan: {powerplan}, sleep: {sleep}s (Temp: {temperature}°C, Trend: {trend})")
        return {'powerplan': powerplan, 'sleep': sleep}

    def apply_optimal_power_plan(self, temperature: Optional[float], trend: Optional[str] = None) -> bool:
        """Determines and applies the optimal power plan based on temperature, trend and apps."""
        # O(DeterminePlan) + O(SetPlan)
        recommendation = self.determine_optimal_power_plan(temperature, trend)
        optimal_plan_name = recommendation['powerplan']
        # The sleep value is returned by determine_optimal_power_plan but not used here.
        # The caller (e.g., the main loop) should handle the sleep duration.
        logging.info(f"CPU Controller ({self.device_id}): Applying optimal power plan: {optimal_plan_name}")
        return self.set_power_plan(optimal_plan_name)

    def apply_settings(self, settings: Dict[str, Any]) -> bool:
        """Apply specified settings to the CPU.

        Supports 'power_plan' for direct setting and 'auto_power_plan'
        which requires 'temperature' and optionally accepts 'trend'
        in the settings dict.
        """
        # O(N * P) where N is number of settings and P is complexity of applying each
        overall_success = True
        settings_applied_count = 0
        original_settings = settings.copy() # Keep original for logging

        # Handle automatic power plan switching first if requested
        if "auto_power_plan" in settings and settings.get("auto_power_plan") is True:
            if "temperature" in settings and isinstance(settings["temperature"], (int, float)):
                temp = settings["temperature"]
                # Get optional trend from settings
                trend = settings.get("trend")
                if trend and not isinstance(trend, str):
                    logging.warning(f"CPU Controller ({self.device_id}): Invalid type for 'trend' setting: {type(trend)}. Ignoring trend.")
                    trend = None
                elif trend not in [None, "rising", "falling", "stable"]:
                     logging.warning(f"CPU Controller ({self.device_id}): Invalid value for 'trend' setting: '{trend}'. Ignoring trend.")
                     trend = None

                logging.debug(f"CPU Controller ({self.device_id}): Auto power plan triggered with temp {temp}°C, trend '{trend}'.")
                # Pass temperature and trend to apply_optimal_power_plan
                applied = self.apply_optimal_power_plan(temp, trend=trend)
                settings_applied_count += 1
                if not applied:
                    overall_success = False
            else:
                logging.error(f"CPU Controller ({self.device_id}): 'auto_power_plan' requires a valid 'temperature' in settings.")
                overall_success = False
            # Remove auto_power_plan, temperature, and trend keys so they aren't processed below
            settings.pop("auto_power_plan", None)
            settings.pop("temperature", None)
            settings.pop("trend", None) # Remove trend as well

        # Process remaining explicit settings
        for key, value in settings.items():
            applied = False
            if key == "power_plan":
                if isinstance(value, str):
                    # O(SetPlan)
                    applied = self.set_power_plan(value)
                    settings_applied_count += 1
                else:
                     logging.error(f"CPU Controller ({self.device_id}): Invalid type for power_plan setting: {type(value)}. Expected str.")
                     applied = False
            # Add other controllable settings here
            # elif key == "clock_speed":
            #     success = self.set_clock_speed(value) # Hypothetical
            #     if not success:
            #         overall_success = False
            else:
                logging.warning(f"CPU Controller ({self.device_id}): Unsupported setting '{key}'.")
                applied = False # Mark as not applied

            # If we intended to apply this specific setting but failed
            if key in original_settings and not applied and key not in ["auto_power_plan", "temperature", "trend"]:
                 overall_success = False

        # Check if any settings were actually processed
        if settings_applied_count == 0 and "auto_power_plan" not in original_settings:
             logging.warning(f"CPU Controller ({self.device_id}): No applicable settings found in {original_settings}.")
             return False # Return False if no relevant settings were provided

        return overall_success

    def get_available_settings(self) -> Dict[str, Any]:
        """Get available controllable settings and their current values."""
        # O(P) complexity due to reading current settings
        settings = {}
        current_plan = self.get_current_power_plan()
        # Only include current plan if successfully read
        if current_plan is not None:
            settings["power_plan"] = current_plan
        else:
             settings["power_plan"] = None # Indicate reading failed
             
        settings["available_power_plans"] = POWER_PLANS
        
        # Add other readable/controllable settings
        # settings["current_clock_speed"] = self.get_current_clock_speed() # Hypothetical
        
        return settings

    def cleanup(self):
        """Perform any cleanup needed for the CPU controller."""
        # O(1) complexity
        # Usually nothing needed for CPU governor control via /sys
        logging.info(f"Cleaned up controller for CPU (ID: {self.device_id})")


class CpuMonitor(DeviceMonitor):
    """
    Monitors CPU temperature using psutil.sensors_temperatures().
    
    This class specifically targets CPU temperature readings available through 
    psutil.sensors_temperatures() on Linux/FreeBSD systems. It attempts to find the
    most relevant CPU temperature by checking common device names and sensor labels.
    """

    def __init__(
        self,
        device_id: str = "cpu_main",
        monitoring_interval: float = 5.0,
        cpu_temp_sensor_labels: Optional[List[str]] = None,
        cpu_temp_device_names: Optional[List[str]] = None
    ):
        """
        Initialize the CPU monitor.

        Args:
            device_id (str): Unique identifier for the CPU monitor instance.
            monitoring_interval (float): How often to update the status in seconds.
            cpu_temp_sensor_labels (Optional[List[str]]): Specific sensor labels to prioritize 
                for CPU temperature (e.g., ['tdie', 'tctl']). Defaults to common AMD/Intel labels.
            cpu_temp_device_names (Optional[List[str]]): Specific device names to look under
                in psutil.sensors_temperatures() (e.g., ['k10temp', 'coretemp']). Defaults to common ones.
        """
        super().__init__(
            device_id=device_id,
            device_type="cpu",
            monitoring_interval=monitoring_interval,
            tracked_properties=["temperature"] # Track temperature history
        )
                
        # O(1) initialization complexity
        self.cpu_temp_sensor_labels = cpu_temp_sensor_labels if cpu_temp_sensor_labels is not None else list(DEFAULT_CPU_TEMP_SENSOR_LABELS)
        self.cpu_temp_device_names = cpu_temp_device_names if cpu_temp_device_names is not None else list(DEFAULT_CPU_TEMP_DEVICE_NAMES)

        # Check psutil availability during initialization
        if psutil is None:
            logging.warning(f"CPU Monitor ({self.device_id}): psutil not available or import failed. CPU monitoring disabled.")
            self.status.set_error("initialization", "psutil library not available.")
        elif not hasattr(psutil, 'sensors_temperatures'):
            logging.warning(f"CPU Monitor ({self.device_id}): psutil.sensors_temperatures not available on this system. CPU temperature monitoring disabled.")
            self.status.set_error("initialization", "psutil.sensors_temperatures not available.")
        else:
            logging.info(f"CPU Monitor ({self.device_id}): Initialized successfully using psutil.")


    def update_status(self) -> None:
        """
        Update CPU status, primarily focusing on temperature from psutil.
        
        Searches psutil.sensors_temperatures() for known device names and sensor labels
        to find the most likely CPU temperature reading.
        Complexity: O(N*M) where N is the number of sensor devices and M is the average 
        number of sensors per device reported by psutil. Typically small.
        """
        # O(1) check
        if psutil is None or not hasattr(psutil, 'sensors_temperatures'):
            # Already logged warning during init, just ensure status reflects error
            if not self.status.has_error("initialization"):
                # Set error if not already set during init (e.g., if psutil was removed post-init)
                self.status.set_error("temperature", "psutil not available or lacks sensors_temperatures.")
            self.status.update_property("temperature", None) # Explicitly set to None
            return

        cpu_temp: Optional[float] = None
        found_sensor_info: str = "" # For logging which sensor was used

        try:
            # O(P) where P is the cost of the psutil call itself
            all_temps: Dict[str, Any] = psutil.sensors_temperatures()
            
            # --- Search Strategy --- 
            # 1. Prioritize specified device names AND specified sensor labels
            # 2. Check any device name with specified sensor labels
            # 3. Check specified device names with any sensor label (less reliable)
            
            # O(N*M) search loop
            # Strategy 1 & 2 combined: Iterate preferred devices first, then others
            devices_to_check = self.cpu_temp_device_names + [d for d in all_temps if d not in self.cpu_temp_device_names]
            
            for device_name in devices_to_check:
                if device_name in all_temps:
                    sensors = all_temps[device_name]
                    # Sort sensors by preferred label order
                    sensors.sort(key=lambda s: self.cpu_temp_sensor_labels.index(s.label.lower().replace(' ', '_')) 
                                   if s.label and s.label.lower().replace(' ', '_') in self.cpu_temp_sensor_labels 
                                   else float('inf'))
                                   
                    for sensor in sensors:
                        label_lower = sensor.label.lower().replace(' ', '_') if sensor.label else ''
                        # Check if this sensor label is in our preferred list
                        if label_lower in self.cpu_temp_sensor_labels:
                            cpu_temp = sensor.current
                            found_sensor_info = f"{device_name}/{label_lower}"
                            logging.debug(f"CPU Monitor ({self.device_id}): Found potential temp {cpu_temp}°C from {found_sensor_info}")
                            break # Found the best match for this device based on label priority
                if cpu_temp is not None:
                    break # Found the best match overall based on device and label priority

            # Strategy 3: If still no temp, check specified devices for *any* sensor (less reliable)
            if cpu_temp is None:
                logging.debug(f"CPU Monitor ({self.device_id}): No prioritized sensor found, checking specified devices for any sensor.")
                for device_name in self.cpu_temp_device_names:
                    if device_name in all_temps:
                        for sensor in all_temps[device_name]:
                            # Take the first available reading from a prioritized device
                            cpu_temp = sensor.current
                            label_lower = sensor.label.lower().replace(' ', '_') if sensor.label else 'unknown'
                            found_sensor_info = f"{device_name}/{label_lower} (fallback)"
                            logging.debug(f"CPU Monitor ({self.device_id}): Found fallback temp {cpu_temp}°C from {found_sensor_info}")
                            break
                    if cpu_temp is not None:
                        break
                         
            # --- Update Status --- 
            if cpu_temp is not None:
                # O(1) update
                self.status.update_property("temperature", float(cpu_temp))
                self.status.clear_error("temperature") # Clear previous errors if successful
                logging.info(f"CPU Monitor ({self.device_id}): Updated temperature to {cpu_temp:.1f}°C from {found_sensor_info}")
            else:
                # Only set error if no temp found after searching all strategies
                # O(1) update
                if not self.status.has_error("temperature"):
                    self.status.set_error("temperature", "Could not find a suitable CPU temperature sensor.")
                    logging.warning(f"CPU Monitor ({self.device_id}): Could not find CPU temperature sensor via psutil after checking {list(all_temps.keys())}.")
                self.status.update_property("temperature", None) # Ensure it's None if not found

        except Exception as e:
            # O(1) update
            logging.error(f"CPU Monitor ({self.device_id}): Error reading psutil sensors: {e}", exc_info=True)
            self.status.set_error("temperature", f"Error reading psutil sensors: {e}")
            self.status.update_property("temperature", None)

    def get_cpu_temperature(self) -> Optional[float]:
        """Convenience method to get the latest CPU temperature.
        Complexity: O(1)
        """
        # O(1) access
        return self.status.get_property("temperature")

