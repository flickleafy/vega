from abc import ABC, abstractmethod
from typing import Any, Dict


class DeviceController(ABC):
    """
    Abstract base class for device controllers.

    This class defines the interface for all device controllers in the Vega system,
    providing consistent control capabilities across different hardware types.

    Attributes:
        device_id (str): Unique identifier for the controlled device.
        device_type (str): Type of the controlled device.
    """

    def __init__(self, device_id: str, device_type: str, device_name: str = None):
        """
        Initialize a DeviceController.

        Args:
            device_id (str): Unique identifier for the controlled device.
            device_type (str): Type of the controlled device.
        """
        self.device_id = device_id
        self.device_type = device_type
        self.device_name = device_name

    @abstractmethod
    def apply_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Apply the specified settings to the device.

        Args:
            settings (Dict[str, Any]): Dictionary of settings to apply.

        Returns:
            bool: True if settings were successfully applied, False otherwise.
        """
        pass

    @abstractmethod
    def get_available_settings(self) -> Dict[str, Any]:
        """
        Get the available settings and their current values.

        Returns:
            Dict[str, Any]: Dictionary of available settings and their values.
        """
        pass
