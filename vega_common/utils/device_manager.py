from vega_common.utils.device_controller import DeviceController
from vega_common.utils.device_monitor import DeviceMonitor
from vega_common.utils.device_status import DeviceStatus

from typing import Any, Dict, Optional, List


class DeviceManager:
    """
    Manager class for coordinating multiple device monitors and controllers.

    This class provides centralized access to all monitored and controlled devices
    in the Vega system, with support for retrieving status and applying settings.

    Attributes:
        monitors (Dict[str, DeviceMonitor]): Dictionary of registered device monitors.
        controllers (Dict[str, DeviceController]): Dictionary of registered device controllers.
    """

    def __init__(self):
        """Initialize a DeviceManager with empty monitor and controller dictionaries."""
        self.monitors: Dict[str, DeviceMonitor] = {}
        self.controllers: Dict[str, DeviceController] = {}

    def register_monitor(self, monitor: DeviceMonitor) -> None:
        """
        Register a device monitor with the manager.

        Args:
            monitor (DeviceMonitor): The device monitor to register.
        """
        device_key = f"{monitor.device_type}:{monitor.device_id}"
        self.monitors[device_key] = monitor

    def register_controller(self, controller: DeviceController) -> None:
        """
        Register a device controller with the manager.

        Args:
            controller (DeviceController): The device controller to register.
        """
        device_key = f"{controller.device_type}:{controller.device_id}"
        self.controllers[device_key] = controller

    def start_all_monitors(self) -> None:
        """Start all registered device monitors."""
        for monitor in self.monitors.values():
            monitor.start_monitoring()

    def stop_all_monitors(self) -> None:
        """Stop all registered device monitors."""
        for monitor in self.monitors.values():
            monitor.stop_monitoring()

    def get_monitors_by_type(self, device_type: str) -> List[DeviceMonitor]:
        """
        Get all monitors of a specific device type.

        Args:
            device_type (str): The type of device monitors to retrieve.

        Returns:
            List[DeviceMonitor]: List of device monitors matching the specified type.
            
        Time complexity: O(N) where N is the number of registered monitors.
        """
        return [
            monitor 
            for key, monitor in self.monitors.items() 
            if monitor.device_type == device_type
        ]

    def get_device_status(self, device_id: str) -> Optional[DeviceStatus]:
        """
        Get the status of a specific device by its ID.

        Args:
            device_id (str): ID of the device.

        Returns:
            Optional[DeviceStatus]: Device status object or None if device not found.
            
        Time complexity: O(N) where N is the number of registered monitors.
        """
        for monitor in self.monitors.values():
            if monitor.device_id == device_id:
                return monitor.status
        return None

    def get_all_statuses(self) -> List[DeviceStatus]:
        """
        Get the status of all monitored devices.

        Returns:
            List[DeviceStatus]: List of device status objects.
            
        Time complexity: O(N) where N is the number of registered monitors.
        """
        return [monitor.status for monitor in self.monitors.values()]

    def apply_device_settings(
        self, device_type: str, device_id: str, settings: Dict[str, Any]
    ) -> bool:
        """
        Apply settings to a specific device.

        Args:
            device_type (str): Type of the device.
            device_id (str): ID of the device.
            settings (Dict[str, Any]): Settings to apply.

        Returns:
            bool: True if settings were successfully applied, False otherwise.
            
        Time complexity: O(1) for dictionary lookup plus the complexity of apply_settings().
        """
        device_key = f"{device_type}:{device_id}"
        if device_key in self.controllers:
            return self.controllers[device_key].apply_settings(settings)
        return False
