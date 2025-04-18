from vega_common.utils.device_controller import DeviceController
from vega_common.utils.device_monitor import DeviceMonitor


from typing import Any, Dict, Optional


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

    def get_device_status(self, device_type: str, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific device.

        Args:
            device_type (str): Type of the device.
            device_id (str): ID of the device.

        Returns:
            Optional[Dict[str, Any]]: Status dictionary or None if device not found.
        """
        device_key = f"{device_type}:{device_id}"
        if device_key in self.monitors:
            return self.monitors[device_key].get_status_dict()
        return None

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the status of all monitored devices.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of device statuses, keyed by device identifier.
        """
        result = {}
        for device_key, monitor in self.monitors.items():
            result[device_key] = monitor.get_status_dict()
        return result

    def apply_device_settings(self, device_type: str, device_id: str,
                              settings: Dict[str, Any]) -> bool:
        """
        Apply settings to a specific device.

        Args:
            device_type (str): Type of the device.
            device_id (str): ID of the device.
            settings (Dict[str, Any]): Settings to apply.

        Returns:
            bool: True if settings were successfully applied, False otherwise.
        """
        device_key = f"{device_type}:{device_id}"
        if device_key in self.controllers:
            return self.controllers[device_key].apply_settings(settings)
        return False