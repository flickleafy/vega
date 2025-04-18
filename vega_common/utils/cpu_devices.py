"""
Concrete implementation for monitoring CPU metrics using psutil.
"""

import logging
import sys
from typing import List, Optional, Dict, Any

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

