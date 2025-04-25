"""
Concrete implementations for monitoring and controlling liquid cooling devices using liquidctl.

This module provides classes for monitoring and controlling liquid cooling systems
(AIOs, custom loops) that are supported by the liquidctl library.
"""

import logging
import threading
import time
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
from abc import ABCMeta

# Import liquidctl conditionally to handle cases where it's not installed
try:
    import liquidctl.cli as liquidctl_cli
    from liquidctl.driver import BaseDriver
    liquidctl_available = True
except ImportError:
    liquidctl_available = False
    logging.error("liquidctl library not found. Watercooler monitoring/control disabled.")
    # Create dummy BaseDriver class for type hinting when liquidctl is not available
    class BaseDriver(metaclass=ABCMeta):
        pass

from .device_monitor import DeviceMonitor
from .device_controller import DeviceController
from .device_status import DeviceStatus
from .temperature_utils import cpu_temp_to_fan_speed

# Global lock for device operations to prevent concurrent access issues
_liquidctl_lock = threading.Lock()

# Constants for accessing specific data in status arrays
_LIQUID_TEMPERATURE_ROW = 0
_FAN_SPEED_ROW = 1
_PUMP_SPEED_ROW = 2
_VALUE_COLUMN = 1

# Default RGB colors for different temperature ranges
_DEFAULT_COLOR_RANGES = [
    (0, 30, [0, 0, 255]),      # Blue for cold (0-30°C)
    (30, 40, [0, 255, 255]),   # Cyan for cool (30-40°C)
    (40, 45, [0, 255, 0]),     # Green for normal (40-45°C)
    (45, 50, [255, 255, 0]),   # Yellow for warm (45-50°C)
    (50, 55, [255, 128, 0]),   # Orange for hot (50-55°C)
    (55, 100, [255, 0, 0]),    # Red for very hot (55+°C)
]


def find_liquidctl_devices() -> List[BaseDriver]:
    """
    Find all compatible liquidctl devices.
    
    Returns:
        List[BaseDriver]: List of available liquidctl devices or empty list if none found.
        
    Time complexity: O(N) where N is the number of connected USB devices.
    """
    if not liquidctl_available:
        logging.error("Cannot find liquidctl devices: liquidctl library not available.")
        return []
    
    try:
        with _liquidctl_lock:
            devices = list(liquidctl_cli.find_liquidctl_devices())
            logging.debug(f"Found {len(devices)} liquidctl-compatible device(s)")
            return devices
    except Exception as e:
        logging.error(f"Error while searching for liquidctl devices: {e}", exc_info=True)
        return []


def initialize_device(device: BaseDriver) -> bool:
    """
    Initialize a single liquidctl device.
    
    Args:
        device (BaseDriver): The liquidctl device to initialize.
        
    Returns:
        bool: True if initialization was successful, False otherwise.
        
    Time complexity: O(1) for the device operations.
    """
    if not liquidctl_available:
        return False
    
    try:
        with _liquidctl_lock:
            device.connect()
            device.initialize()
            return True
    except Exception as e:
        logging.error(f"Error initializing liquidctl device {device.description}: {e}", exc_info=True)
        return False


def get_device_status(device: BaseDriver) -> Optional[List[Tuple[str, Any, str]]]:
    """
    Get the status of a liquidctl device.
    
    Args:
        device (BaseDriver): The liquidctl device to query.
        
    Returns:
        Optional[List[Tuple[str, Any, str]]]: Status data or None if failed.
        
    Time complexity: O(1) for the device operations.
    """
    if not liquidctl_available:
        return None
    
    try:
        with _liquidctl_lock:
            return device.get_status()
    except Exception as e:
        logging.error(f"Error getting status for liquidctl device {device.description}: {e}", exc_info=True)
        return None


def set_fan_speed(device: BaseDriver, speed: int) -> bool:
    """
    Set the fan speed for a liquidctl device.
    
    Args:
        device (BaseDriver): The liquidctl device to control.
        speed (int): Fan speed percentage (0-100).
        
    Returns:
        bool: True if setting was successful, False otherwise.
        
    Time complexity: O(1) for the device operations.
    """
    if not liquidctl_available:
        return False
    
    try:
        with _liquidctl_lock:
            device.set_fixed_speed("fan", speed)
            return True
    except Exception as e:
        logging.error(f"Error setting fan speed for liquidctl device {device.description}: {e}", exc_info=True)
        return False


def set_pump_speed(device: BaseDriver, speed: int) -> bool:
    """
    Set the pump speed for a liquidctl device if supported.
    
    Args:
        device (BaseDriver): The liquidctl device to control.
        speed (int): Pump speed percentage (0-100).
        
    Returns:
        bool: True if setting was successful, False otherwise.
        
    Time complexity: O(1) for the device operations.
    """
    if not liquidctl_available:
        return False
    
    try:
        with _liquidctl_lock:
            device.set_fixed_speed("pump", speed)
            return True
    except Exception as e:
        # Some devices might not support separate pump speed control
        logging.warning(f"Could not set pump speed for device {device.description}: {e}")
        return False


def set_led_color(device: BaseDriver, r: int, g: int, b: int, mode: str = "fixed", speed: str = "normal") -> bool:
    """
    Set the LED color for a liquidctl device.
    
    Args:
        device (BaseDriver): The liquidctl device to control.
        r (int): Red component (0-255).
        g (int): Green component (0-255).
        b (int): Blue component (0-255).
        mode (str, optional): Lighting mode (fixed, breathing, etc.). Defaults to "fixed".
        speed (str, optional): Animation speed for dynamic modes. Defaults to "normal".
        
    Returns:
        bool: True if setting was successful, False otherwise.
        
    Time complexity: O(1) for the device operations.
    """
    if not liquidctl_available:
        return False
    
    # Not all devices support the same lighting channels
    # Try common channel names used across different liquidctl devices
    channels = ["sync", "led", "logo", "ring", "external"]
    success = False
    
    try:
        with _liquidctl_lock:
            for channel in channels:
                try:
                    if mode == "fixed":
                        device.set_color(channel, mode, [r, g, b])
                    else:
                        device.set_color(channel, mode, [r, g, b], speed=speed)
                    success = True
                except Exception:
                    # Just try the next channel if this one failed
                    pass
            
            return success
    except Exception as e:
        logging.error(f"Error setting LED color for liquidctl device {device.description}: {e}", exc_info=True)
        return False


def get_temperature_color(temperature: float, 
                          color_ranges: List[Tuple[float, float, List[int]]] = None) -> List[int]:
    """
    Get an RGB color based on the temperature.
    
    Args:
        temperature (float): Temperature in degrees Celsius.
        color_ranges (List[Tuple[float, float, List[int]]], optional): Custom color range mapping.
            Each tuple contains (min_temp, max_temp, [r, g, b]). Defaults to None.
        
    Returns:
        List[int]: RGB color values [r, g, b].
        
    Time complexity: O(N) where N is the number of color ranges.
    """
    if color_ranges is None:
        color_ranges = _DEFAULT_COLOR_RANGES
        
    # Default to first color if temperature is too low, or last color if too high
    result_color = color_ranges[0][2] if temperature < color_ranges[0][0] else color_ranges[-1][2]
    
    # Find the matching range
    for min_temp, max_temp, color in color_ranges:
        if min_temp <= temperature < max_temp:
            result_color = color
            break
            
    return result_color


class WatercoolerMonitor(DeviceMonitor):
    """
    Monitor for liquid cooling devices using the liquidctl library.
    
    Provides temperature, fan speed, pump speed and other metrics from compatible
    liquid cooling devices.
    """

    def __init__(self, 
                 device_index: int = 0, 
                 monitoring_interval: float = 3.0,
                 device_id: Optional[str] = None):
        """
        Initialize the watercooler monitor.
        
        Args:
            device_index (int, optional): Index of the liquidctl device to monitor. Defaults to 0.
            monitoring_interval (float, optional): Update interval in seconds. Defaults to 3.0.
            device_id (Optional[str], optional): Custom device ID. If None, will be generated. 
                Defaults to None.
                
        Raises:
            RuntimeError: If liquidctl is not available or device initialization fails.
            IndexError: If the device_index is invalid.
            
        Time complexity: O(N) where N is the number of connected USB devices.
        """
        if not liquidctl_available:
            raise RuntimeError("liquidctl library is not available")
            
        # Find all compatible devices
        self.all_devices = find_liquidctl_devices()
        if not self.all_devices:
            raise RuntimeError("No compatible liquid cooling devices found")
            
        if device_index < 0 or device_index >= len(self.all_devices):
            raise IndexError(f"Invalid device index {device_index}. Found {len(self.all_devices)} devices")
            
        # Get the specific device we're monitoring
        self.device = self.all_devices[device_index]
        self.device_index = device_index
        
        # Generate device ID if not provided
        if device_id is None:
            device_id = f"watercooler_{device_index}"
            
        # Try to get a better name from the device description
        device_name = "Unknown Watercooler"
        if hasattr(self.device, "description") and self.device.description:
            device_name = self.device.description
            
        # Skip LED-only devices
        if device_name and "LED" in device_name:
            raise RuntimeError(f"Device {device_name} appears to be an LED controller, not a watercooler")
            
        # Initialize the device
        if not initialize_device(self.device):
            raise RuntimeError(f"Failed to initialize device {device_name}")
            
        # Call base class initializer
        super().__init__(
            device_id=device_id,
            device_type="watercooler",
            device_name=device_name,
            monitoring_interval=monitoring_interval,
            tracked_properties=[
                "liquid_temperature",
                "fan_speed",
                "pump_speed",
                "fan_duty",
                "pump_duty",
            ],
        )
        
        # Get initial status to verify it works
        initial_status = get_device_status(self.device)
        if initial_status is None:
            raise RuntimeError(f"Failed to get initial status for device {device_name}")
            
        logging.info(f"Initialized monitor for {device_name} (ID: {device_id})")
    
    def update_status(self) -> None:
        """
        Update the watercooler status with fresh data.
        
        This method retrieves the current status from the liquidctl device
        and updates the corresponding properties in the DeviceStatus object.
        
        Time complexity: O(1) for device operations + O(N) for processing status entries.
        """
        if not liquidctl_available:
            self.status.set_error("general", "liquidctl library not available")
            return
        
        try:
            # Get raw status data from the device
            status_data = get_device_status(self.device)
            
            if status_data is None:
                self.status.set_error("general", "Failed to get device status")
                return
                
            # Clear any previous general errors since we got a valid status
            self.status.clear_error("general")
            
            # Process each status entry
            # Typical entries are like: ('Liquid temperature', 30.5, '°C')
            liquid_temp = None
            fan_speed = None
            pump_speed = None
            
            for entry in status_data:
                if len(entry) >= 3:  # Ensure we have (name, value, unit)
                    name, value, unit = entry[0].lower(), entry[1], entry[2]
                    
                    # Match status entries to our tracked properties
                    if "liquid" in name and "temp" in name:
                        liquid_temp = float(value) if isinstance(value, (int, float)) else None
                        self.status.update_property("liquid_temperature", liquid_temp)
                        
                    elif "fan" in name and ("rpm" in name or "speed" in name or unit.lower() == "rpm"):
                        fan_speed = int(value) if isinstance(value, (int, float)) else None
                        self.status.update_property("fan_speed", fan_speed)
                        
                    elif "fan" in name and ("duty" in name or "percent" in name or unit == "%"):
                        fan_duty = int(value) if isinstance(value, (int, float)) else None
                        self.status.update_property("fan_duty", fan_duty)
                        
                    elif "pump" in name and ("rpm" in name or "speed" in name or unit.lower() == "rpm"):
                        pump_speed = int(value) if isinstance(value, (int, float)) else None
                        self.status.update_property("pump_speed", pump_speed)
                        
                    elif "pump" in name and ("duty" in name or "percent" in name or unit == "%"):
                        pump_duty = int(value) if isinstance(value, (int, float)) else None
                        self.status.update_property("pump_duty", pump_duty)
                        
            # Alternative approach using fixed indices from the original implementation
            # For devices where the status format is fixed and known
            if liquid_temp is None and len(status_data) > _LIQUID_TEMPERATURE_ROW:
                liquid_temp_entry = status_data[_LIQUID_TEMPERATURE_ROW]
                if len(liquid_temp_entry) > _VALUE_COLUMN:
                    value = liquid_temp_entry[_VALUE_COLUMN]
                    if isinstance(value, (int, float)):
                        self.status.update_property("liquid_temperature", float(value))
                    
            if fan_speed is None and len(status_data) > _FAN_SPEED_ROW:
                fan_speed_entry = status_data[_FAN_SPEED_ROW]
                if len(fan_speed_entry) > _VALUE_COLUMN:
                    value = fan_speed_entry[_VALUE_COLUMN]
                    if isinstance(value, (int, float)):
                        self.status.update_property("fan_speed", int(value))
                    
            if pump_speed is None and len(status_data) > _PUMP_SPEED_ROW:
                pump_speed_entry = status_data[_PUMP_SPEED_ROW]
                if len(pump_speed_entry) > _VALUE_COLUMN:
                    value = pump_speed_entry[_VALUE_COLUMN]
                    if isinstance(value, (int, float)):
                        self.status.update_property("pump_speed", int(value))
                        
            # Mark status as updated
            self.status.mark_updated()
            
        except Exception as e:
            logging.error(f"Error updating watercooler status for {self.device_id}: {e}", exc_info=True)
            self.status.set_error("general", f"Error updating status: {str(e)}")
    
    def get_liquid_temperature(self) -> Optional[float]:
        """
        Get the current liquid temperature.
        
        Returns:
            Optional[float]: Liquid temperature in degrees Celsius or None if not available.
            
        Time complexity: O(1) for property access.
        """
        return self.status.get_property("liquid_temperature")
    
    def get_fan_speed(self) -> Optional[int]:
        """
        Get the current fan speed in RPM.
        
        Returns:
            Optional[int]: Fan speed in RPM or None if not available.
            
        Time complexity: O(1) for property access.
        """
        return self.status.get_property("fan_speed")
    
    def get_pump_speed(self) -> Optional[int]:
        """
        Get the current pump speed in RPM.
        
        Returns:
            Optional[int]: Pump speed in RPM or None if not available.
            
        Time complexity: O(1) for property access.
        """
        return self.status.get_property("pump_speed")
    
    def cleanup(self) -> None:
        """
        Release resources used by the watercooler monitor.
        
        This method ensures proper shutdown of any resources or connections
        that the monitor may have opened.
        
        Time complexity: O(1) for simple resource cleanup.
        """
        # Stop monitoring if active
        if hasattr(self, "is_monitoring") and self.is_monitoring:
            self.stop_monitoring()
        
        # Clear any cached data
        if hasattr(self, "status"):
            self.status.clear_errors()
            
        logging.info(f"Cleaned up monitor for watercooler (ID: {self.device_id})")


class WatercoolerController(DeviceController):
    """
    Controller for liquid cooling devices using the liquidctl library.
    
    Provides methods to control fan speed, pump speed, and lighting effects.
    """
    
    def __init__(self, 
                 device_index: int = 0,
                 device_id: Optional[str] = None):
        """
        Initialize the watercooler controller.
        
        Args:
            device_index (int, optional): Index of the liquidctl device to control. Defaults to 0.
            device_id (Optional[str], optional): Custom device ID. If None, will be generated.
                Defaults to None.
                
        Raises:
            RuntimeError: If liquidctl is not available or device initialization fails.
            IndexError: If the device_index is invalid.
            
        Time complexity: O(N) where N is the number of connected USB devices.
        """
        if not liquidctl_available:
            raise RuntimeError("liquidctl library is not available")
            
        # Find all compatible devices
        self.all_devices = find_liquidctl_devices()
        if not self.all_devices:
            raise RuntimeError("No compatible liquid cooling devices found")
            
        if device_index < 0 or device_index >= len(self.all_devices):
            raise IndexError(f"Invalid device index {device_index}. Found {len(self.all_devices)} devices")
            
        # Get the specific device we're controlling
        self.device = self.all_devices[device_index]
        self.device_index = device_index
        
        # Generate device ID if not provided
        if device_id is None:
            device_id = f"watercooler_{device_index}"
            
        # Try to get a better name from the device description
        device_name = "Unknown Watercooler"
        if hasattr(self.device, "description") and self.device.description:
            device_name = self.device.description
            
        # Skip LED-only devices
        if device_name and "LED" in device_name:
            raise RuntimeError(f"Device {device_name} appears to be an LED controller, not a watercooler")
            
        # Initialize the device
        if not initialize_device(self.device):
            raise RuntimeError(f"Failed to initialize device {device_name}")
            
        # Call base class initializer
        super().__init__(
            device_id=device_id,
            device_type="watercooler",
            device_name=device_name,
        )
        
        # Store current lighting color for status reporting
        self.current_color = [0, 0, 0]
        self.current_fan_speed = None
        self.current_pump_speed = None
        
        logging.info(f"Initialized controller for {device_name} (ID: {device_id})")
    
    def set_fan_speed(self, speed: int) -> bool:
        """
        Set the fan speed for the watercooling device.
        
        Args:
            speed (int): Fan speed percentage (0-100).
            
        Returns:
            bool: True if successful, False otherwise.
            
        Time complexity: O(1) for device operation.
        """
        # Ensure speed is within valid range
        speed = max(0, min(100, int(speed)))
        
        success = set_fan_speed(self.device, speed)
        if success:
            self.current_fan_speed = speed
            logging.debug(f"Set fan speed to {speed}% for {self.device_id}")
        else:
            logging.warning(f"Failed to set fan speed for {self.device_id}")
            
        return success
    
    def set_pump_speed(self, speed: int) -> bool:
        """
        Set the pump speed for the watercooling device if supported.
        
        Args:
            speed (int): Pump speed percentage (0-100).
            
        Returns:
            bool: True if successful, False otherwise.
            
        Time complexity: O(1) for device operation.
        """
        # Ensure speed is within valid range
        speed = max(0, min(100, int(speed)))
        
        success = set_pump_speed(self.device, speed)
        if success:
            self.current_pump_speed = speed
            logging.debug(f"Set pump speed to {speed}% for {self.device_id}")
        
        return success
    
    def set_lighting_color(self, r: int, g: int, b: int, mode: str = "fixed") -> bool:
        """
        Set the LED lighting color for the watercooling device.
        
        Args:
            r (int): Red component (0-255).
            g (int): Green component (0-255).
            b (int): Blue component (0-255).
            mode (str, optional): Lighting mode. Defaults to "fixed".
            
        Returns:
            bool: True if successful, False otherwise.
            
        Time complexity: O(1) for device operation.
        """
        # Ensure color components are within valid range
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))
        
        success = set_led_color(self.device, r, g, b, mode)
        if success:
            self.current_color = [r, g, b]
            logging.debug(f"Set lighting color to [{r},{g},{b}] for {self.device_id}")
        else:
            logging.warning(f"Failed to set lighting color for {self.device_id}")
            
        return success
    
    def set_lighting_by_temperature(self, temperature: float) -> bool:
        """
        Set the LED lighting color based on temperature.
        
        Args:
            temperature (float): Temperature in degrees Celsius.
            
        Returns:
            bool: True if successful, False otherwise.
            
        Time complexity: O(N) where N is the number of color temperature ranges.
        """
        rgb_color = get_temperature_color(temperature)
        return self.set_lighting_color(*rgb_color)
    
    def apply_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Apply specified settings to the watercooling device.
        
        Args:
            settings (Dict[str, Any]): Dictionary of settings to apply.
                Supported keys:
                - 'fan_speed': Fan speed percentage (0-100)
                - 'pump_speed': Pump speed percentage (0-100)
                - 'lighting_color': RGB color as [r, g, b] list
                - 'lighting_mode': Lighting mode string
                - 'temperature': Temperature for automatic color setting
                - 'auto_fan': If True, will set fan speed based on temperature
            
        Returns:
            bool: True if all settings were applied successfully, False otherwise.
            
        Time complexity: O(1) for each setting applied.
        """
        success = True
        applied_any = False
        
        # Handle fan speed setting
        if "fan_speed" in settings:
            fan_speed = settings["fan_speed"]
            if isinstance(fan_speed, (int, float)):
                fan_result = self.set_fan_speed(int(fan_speed))
                success = success and fan_result
                applied_any = True
        
        # Handle auto fan speed based on temperature
        elif "auto_fan" in settings and settings["auto_fan"] and "temperature" in settings:
            temp = settings["temperature"]
            if isinstance(temp, (int, float)):
                # Calculate fan speed based on temperature
                fan_speed = cpu_temp_to_fan_speed(temp)
                fan_result = self.set_fan_speed(fan_speed)
                success = success and fan_result
                applied_any = True
        
        # Handle pump speed setting
        if "pump_speed" in settings:
            pump_speed = settings["pump_speed"]
            if isinstance(pump_speed, (int, float)):
                pump_result = self.set_pump_speed(int(pump_speed))
                # Don't fail the overall operation if pump control isn't supported
                applied_any = True
        
        # Handle lighting color setting
        if "lighting_color" in settings:
            color = settings["lighting_color"]
            mode = settings.get("lighting_mode", "fixed")
            
            if isinstance(color, (list, tuple)) and len(color) >= 3:
                r, g, b = color[0], color[1], color[2]
                lighting_result = self.set_lighting_color(r, g, b, mode)
                success = success and lighting_result
                applied_any = True
        
        # Handle automatic lighting based on temperature
        elif "temperature" in settings and "auto_lighting" in settings and settings["auto_lighting"]:
            temp = settings["temperature"]
            if isinstance(temp, (int, float)):
                lighting_result = self.set_lighting_by_temperature(temp)
                success = success and lighting_result
                applied_any = True
        
        # Return False if no settings were recognized/applied
        return success if applied_any else False
    
    def get_available_settings(self) -> Dict[str, Any]:
        """
        Get available controllable settings and their current values.
        
        Returns:
            Dict[str, Any]: Dictionary of available settings and their values.
            
        Time complexity: O(1) for gathering settings.
        """
        settings = {
            "device_name": self.device_name,
            "device_id": self.device_id,
            "controllable_settings": [
                "fan_speed",
                "pump_speed",
                "lighting_color",
                "lighting_mode",
                "auto_fan",
                "auto_lighting",
            ],
            "current_fan_speed": self.current_fan_speed,
            "current_pump_speed": self.current_pump_speed,
            "current_lighting_color": self.current_color,
            "supported_lighting_modes": ["fixed", "breathing", "pulse", "spectrum"],
        }
        
        return settings
    
    def cleanup(self) -> None:
        """
        Perform any cleanup needed for the watercooler controller.
        
        Time complexity: O(1) for simple resource cleanup.
        """
        logging.info(f"Cleaned up controller for watercooler (ID: {self.device_id})")


# Example usage (for testing purposes, would normally be used by DeviceManager)
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    if not liquidctl_available:
        print("liquidctl library not available. Cannot continue.")
        exit(1)
    
    # Find devices
    devices = find_liquidctl_devices()
    if not devices:
        print("No compatible liquid cooling devices found.")
        exit(1)
        
    print(f"Found {len(devices)} liquidctl-compatible device(s):")
    for i, dev in enumerate(devices):
        print(f"  {i}: {dev.description}")
    
    try:
        # Initialize monitor and controller for the first device
        monitor = WatercoolerMonitor(device_index=0, monitoring_interval=2.0)
        controller = WatercoolerController(device_index=0)
        
        # Get initial status
        monitor.update_status()
        print("\nCurrent status:")
        status_dict = monitor.status.to_dict()
        for key, value in status_dict.items():
            if key not in ["device_id", "device_type", "last_update"]:
                print(f"  {key}: {value}")
        
        # Demonstrate control
        print("\nTesting fan control...")
        controller.set_fan_speed(50)
        time.sleep(2)
        
        print("Testing LED control...")
        controller.set_lighting_color(0, 0, 255)  # Blue
        time.sleep(2)
        controller.set_lighting_by_temperature(45)  # Should be green
        
        # Monitor for a few cycles
        print("\nMonitoring for 10 seconds...")
        monitor.start_monitoring()
        time.sleep(10)
        monitor.stop_monitoring()
        
        # Clean up
        print("\nCleaning up...")
        monitor.cleanup()
        controller.cleanup()
        
    except Exception as e:
        print(f"Error during example execution: {e}")
        
    print("\nExample completed.")