"""
Concrete implementations for monitoring and controlling NVIDIA GPUs using NVML.
"""

import logging
import threading
import time  # Added for example usage
from typing import Optional, Tuple, List, Dict, Any

# Import pynvml from the installed package, not the removed vendored copy
try:
    import pynvml
except ImportError:
    pynvml = None  # Allow graceful failure if NVML is not installed/available
    logging.error("pynvml library not found. NVIDIA GPU monitoring/control disabled.")

from .device_monitor import DeviceMonitor
from .device_controller import DeviceController
from .device_status import DeviceStatus

# Global lock for NVML initialization/shutdown
# Complexity: O(1) for lock operations
_nvml_lock = threading.Lock()
_nvml_init_count = 0


def _initialize_nvml_safe():
    """Initializes NVML if not already initialized, managing a global count."""
    # Complexity: O(1) average case for lock acquisition
    global _nvml_init_count
    with _nvml_lock:
        if pynvml is None:
            raise NVMLError("pynvml library is not available.")
        if _nvml_init_count == 0:
            try:
                pynvml.nvmlInit()
                logging.debug("NVML initialized.")
            except pynvml.NVMLError as error:
                logging.error(f"Failed to initialize NVML: {str(error)}")
                raise NVMLError(f"Failed to initialize NVML: {str(error)}") from error  # Raise custom error
        _nvml_init_count += 1


def _shutdown_nvml_safe():
    """Shutdown NVML if this is the last user."""
    # Complexity: O(1) average case for lock acquisition
    global _nvml_init_count
    with _nvml_lock:
        if pynvml is None or _nvml_init_count == 0:
            return  # Not initialized or already shut down
        _nvml_init_count -= 1
        if _nvml_init_count == 0:
            try:
                pynvml.nvmlShutdown()
                logging.debug("NVML shut down.")
            except pynvml.NVMLError as error:
                # Log error but don't raise, as shutdown failure is less critical
                logging.error(f"Failed to shut down NVML: {str(error)}")


class NVMLError(Exception):
    """Custom exception for NVML related errors."""
    pass

# Get GPU list
# nvidia-settings -q gpus

# Get GPU list
# nvidia-smi -L

# Get GPU temperature
# nvidia-settings -q [gpu:0]/GPUCoreTemp | grep xxx-master

# Get GPU temperature
# nvidia-smi -i 0 --query-gpu=temperature.gpu --format=csv,noheader

class NvidiaGpuMonitor(DeviceMonitor):
    """
    Monitor for NVIDIA GPUs using the NVML library.

    Provides temperature, utilization, fan speed, and other metrics.
    """

    def __init__(self, device_index: int, monitoring_interval: float = 3.0):
        """
        Initialize the NVIDIA GPU monitor.

        Args:
            device_index (int): Index of the GPU in the system (0, 1, ...).
            monitoring_interval (float): Update interval in seconds.

        Raises:
            NVMLError: If NVML initialization fails or device handle cannot be obtained.
            ValueError: If device_index is invalid.
        """
        # Complexity: O(1) typical NVML call time
        if pynvml is None:
            raise NVMLError("pynvml library is not available.")

        _initialize_nvml_safe()  # Ensure NVML is initialized

        self.device_index = device_index
        self.handle = None
        device_id = f"nvidia_gpu_{device_index}"  # Default ID
        device_name = "Unknown NVIDIA GPU"

        try:
            # Validate device_index
            device_count = pynvml.nvmlDeviceGetCount()
            if not (0 <= device_index < device_count):
                raise ValueError(f"Invalid device_index {device_index}. Found {device_count} devices.")

            self.handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_index)
            # Use PCI bus ID as a more stable device_id
            pci_info = pynvml.nvmlDeviceGetPciInfo(self.handle)
            # Format busId to be filesystem/URL safe if needed, but keep original for display
            device_id = pci_info.busId.decode('utf-8')  # busId is bytes
            device_name = pynvml.nvmlDeviceGetName(self.handle).decode('utf-8')

        except pynvml.NVMLError as error:
            _shutdown_nvml_safe()  # Decrement count if init succeeded but handle failed
            logging.error(f"Failed to get handle for GPU {device_index}: {str(error)}")
            raise NVMLError(f"Failed to get handle for GPU {device_index}: {str(error)}") from error
        except ValueError as error:
            _shutdown_nvml_safe()  # Decrement count if init failed due to invalid index
            logging.error(f"Invalid GPU index {device_index}: {str(error)}")
            raise error  # Re-raise ValueError

        super().__init__(
            device_id=device_id,
            device_type="gpu",
            device_name=device_name,
            monitoring_interval=monitoring_interval,
            tracked_properties=[
                "temperature", "fan_speed_1", "fan_speed_2",
                "gpu_utilization", "memory_utilization"
            ]
        )
        logging.info(f"Initialized monitor for {self.device_name} (ID: {self.device_id})")

    def update_status(self):
        """
        Update GPU status with fresh data from NVML.

        Complexity: O(1) for NVML calls.
        """
        if self.handle is None:
            logging.warning(f"Skipping update for GPU {self.device_id}: NVML handle not available.")
            return

        try:
            # --- Temperature ---
            try:
                temp = pynvml.nvmlDeviceGetTemperature(self.handle, pynvml.NVML_TEMPERATURE_GPU)
                self.status.update_property("temperature", temp)
            except pynvml.NVMLError as e:
                # Check if the error is 'NOT_SUPPORTED'
                if hasattr(pynvml, 'NVML_ERROR_NOT_SUPPORTED') and isinstance(e, pynvml.NVMLError) and e.args[0] == pynvml.NVML_ERROR_NOT_SUPPORTED:
                    logging.debug(f"Temperature sensor not supported for {self.device_id}.")
                    self.status.update_property("temperature", None, is_error=False)  # Mark as None, not error
                else:
                    logging.warning(f"Could not get temperature for {self.device_id}: {e}")
                    self.status.update_property("temperature", None, is_error=True)

            # --- Fan Speed ---
            try:
                num_fans = pynvml.nvmlDeviceGetNumFans(self.handle)
                fan1 = None
                fan2 = None
                if num_fans >= 1:
                    try:
                        fan1 = pynvml.nvmlDeviceGetFanSpeed_v2(self.handle, 0)
                    except pynvml.NVMLError as e_fan1:
                        if hasattr(pynvml, 'NVML_ERROR_NOT_SUPPORTED') and isinstance(e_fan1, pynvml.NVMLError) and e_fan1.args[0] == pynvml.NVML_ERROR_NOT_SUPPORTED:
                            logging.debug(f"Fan 0 speed not supported for {self.device_id}.")
                        else:
                            raise e_fan1  # Re-raise other errors
                if num_fans >= 2:
                    try:
                        fan2 = pynvml.nvmlDeviceGetFanSpeed_v2(self.handle, 1)
                    except pynvml.NVMLError as e_fan2:
                        if hasattr(pynvml, 'NVML_ERROR_NOT_SUPPORTED') and isinstance(e_fan2, pynvml.NVMLError) and e_fan2.args[0] == pynvml.NVML_ERROR_NOT_SUPPORTED:
                            logging.debug(f"Fan 1 speed not supported for {self.device_id}.")
                        else:
                            raise e_fan2  # Re-raise other errors

                self.status.update_property("fan_speed_1", fan1)
                self.status.update_property("fan_speed_2", fan2)
            except pynvml.NVMLError as e:
                logging.warning(f"Could not get fan speed for {self.device_id}: {e}")
                self.status.update_property("fan_speed_1", None, is_error=True)
                self.status.update_property("fan_speed_2", None, is_error=True)

            # --- Utilization ---
            try:
                util = pynvml.nvmlDeviceGetUtilizationRates(self.handle)
                self.status.update_property("gpu_utilization", util.gpu)
                self.status.update_property("memory_utilization", util.memory)
            except pynvml.NVMLError as e:
                if hasattr(pynvml, 'NVML_ERROR_NOT_SUPPORTED') and isinstance(e, pynvml.NVMLError) and e.args[0] == pynvml.NVML_ERROR_NOT_SUPPORTED:
                    logging.debug(f"Utilization rates not supported for {self.device_id}.")
                    self.status.update_property("gpu_utilization", None, is_error=False)
                    self.status.update_property("memory_utilization", None, is_error=False)
                else:
                    logging.warning(f"Could not get utilization for {self.device_id}: {e}")
                    self.status.update_property("gpu_utilization", None, is_error=True)
                    self.status.update_property("memory_utilization", None, is_error=True)

            # Mark status as updated successfully
            self.status.mark_updated()

        except pynvml.NVMLError as e:
            logging.error(f"NVML error during update for {self.device_id}: {e}")
            # Mark all properties as error state if a general NVML error occurs
            for prop in self.tracked_properties:
                self.status.update_property(prop, None, is_error=True)
            self.status.mark_updated()  # Mark update attempt even if failed

    def cleanup(self):
        """Release NVML resources."""
        # Complexity: O(1)
        _shutdown_nvml_safe()
        logging.info(f"Cleaned up monitor for {self.device_id}")


# Set GPU fan speed %
# nvidia-settings -a [gpu:0]/GPUFanControlState=1 -a [fan:0]/GPUTargetFanSpeed=20

class NvidiaGpuController(DeviceController):
    """
    Controller for NVIDIA GPUs using the NVML library.

    Provides methods to set fan speeds.
    """

    def __init__(self, device_index: int):
        """
        Initialize the NVIDIA GPU controller.

        Args:
            device_index (int): Index of the GPU in the system (0, 1, ...).

        Raises:
            NVMLError: If NVML initialization fails or device handle cannot be obtained.
            ValueError: If device_index is invalid.
        """
        # Complexity: O(1) typical NVML call time
        if pynvml is None:
            raise NVMLError("pynvml library is not available.")

        _initialize_nvml_safe()  # Ensure NVML is initialized

        self.device_index = device_index
        self.handle = None
        device_id = f"nvidia_gpu_{device_index}"  # Default ID
        device_name = "Unknown NVIDIA GPU"

        try:
            # Validate device_index
            device_count = pynvml.nvmlDeviceGetCount()
            if not (0 <= device_index < device_count):
                raise ValueError(f"Invalid device_index {device_index}. Found {device_count} devices.")

            self.handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_index)
            pci_info = pynvml.nvmlDeviceGetPciInfo(self.handle)
            device_id = pci_info.busId.decode('utf-8')
            device_name = pynvml.nvmlDeviceGetName(self.handle).decode('utf-8')

        except pynvml.NVMLError as error:
            _shutdown_nvml_safe()
            logging.error(f"Failed to get handle for GPU controller {device_index}: {str(error)}")
            raise NVMLError(f"Failed to get handle for GPU controller {device_index}: {str(error)}") from error
        except ValueError as error:
            _shutdown_nvml_safe()
            logging.error(f"Invalid GPU index {device_index}: {str(error)}")
            raise error

        super().__init__(device_id=device_id, device_type="gpu", device_name=device_name)
        logging.info(f"Initialized controller for {self.device_name} (ID: {self.device_id})")

    def set_fan_speed(self, speed1: int, speed2: Optional[int] = None) -> bool:
        """
        Set the speed for the GPU fans.

        Args:
            speed1 (int): Target speed percentage for fan 0 (or the only fan).
            speed2 (int, optional): Target speed percentage for fan 1. If None,
                                     speed1 is used for fan 1 if it exists.

        Returns:
            bool: True if successful, False otherwise.

        Complexity: O(1) for NVML calls.
        """
        if self.handle is None:
            logging.error(f"Cannot set fan speed for {self.device_id}: NVML handle not available.")
            return False

        success = True
        try:
            num_fans = pynvml.nvmlDeviceGetNumFans(self.handle)

            # Clamp speeds
            speed1 = max(0, min(100, speed1))
            if speed2 is not None:
                speed2 = max(0, min(100, speed2))
            else:
                speed2 = speed1  # Default second fan to first fan's speed if not specified

            if num_fans >= 1:
                try:
                    pynvml.nvmlDeviceSetFanSpeed_v2(self.handle, 0, speed1)
                    logging.debug(f"Set {self.device_id} Fan 0 speed to {speed1}%")
                except pynvml.NVMLError as error:
                    # Some cards report fans but don't allow setting speed
                    if hasattr(pynvml, 'NVML_ERROR_NOT_SUPPORTED') and isinstance(error, pynvml.NVMLError) and error.args[0] == pynvml.NVML_ERROR_NOT_SUPPORTED:
                        logging.warning(f"Fan 0 speed control not supported for {self.device_id}.")
                        # Don't mark as failure if control is just not supported
                    else:
                        logging.warning(f"Failed to set fan 0 speed for {self.device_id}: {str(error)}")
                        success = False  # Mark as partially failed if one fan fails

            if num_fans >= 2:
                try:
                    pynvml.nvmlDeviceSetFanSpeed_v2(self.handle, 1, speed2)
                    logging.debug(f"Set {self.device_id} Fan 1 speed to {speed2}%")
                except pynvml.NVMLError as error:
                    if hasattr(pynvml, 'NVML_ERROR_NOT_SUPPORTED') and isinstance(error, pynvml.NVMLError) and error.args[0] == pynvml.NVML_ERROR_NOT_SUPPORTED:
                        logging.warning(f"Fan 1 speed control not supported for {self.device_id}.")
                    else:
                        logging.warning(f"Failed to set fan 1 speed for {self.device_id}: {str(error)}")
                        success = False

        except pynvml.NVMLError as error:
            logging.error(f"NVML error setting fan speed for {self.device_id}: {str(error)}")
            success = False

        return success

    def cleanup(self):
        """Release NVML resources."""
        # Complexity: O(1)
        _shutdown_nvml_safe()
        logging.info(f"Cleaned up controller for {self.device_id}")


# Example usage (for testing purposes, would normally be used by DeviceManager)
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    monitors: List[NvidiaGpuMonitor] = []
    controllers: List[NvidiaGpuController] = []
    gpu_count = 0
    try:
        _initialize_nvml_safe()  # Initial check
        gpu_count = pynvml.nvmlDeviceGetCount()
        _shutdown_nvml_safe()  # Close initial check
        print(f"Found {gpu_count} NVIDIA GPUs.")

    except NVMLError as e:
        print(f"NVML Error during detection: {e}")
        gpu_count = 0  # Ensure count is 0 if detection fails

    if gpu_count > 0:
        for i in range(gpu_count):
            try:
                monitor = NvidiaGpuMonitor(device_index=i, monitoring_interval=1.0)
                monitors.append(monitor)
                controller = NvidiaGpuController(device_index=i)
                controllers.append(controller)
            except (NVMLError, ValueError) as e:
                print(f"Could not initialize monitor/controller for GPU {i}: {e}")

        if monitors:
            print("\n--- Monitoring (Example: First GPU) ---")
            try:
                monitors[0].update_status()
                status_dict = monitors[0].status.get_all_properties()
                print(f"GPU {monitors[0].device_id} Status:")
                for key, value in status_dict.items():
                    print(f"  {key}: {value}")

            except Exception as e:
                print(f"Error during monitoring example: {e}")

        if controllers:
            print("\n--- Controlling (Example: First GPU) ---")
            try:
                print("Attempting to set fan speed to 50% for GPU 0 (Fan 0 and 1)")
                success = controllers[0].set_fan_speed(50)
                print(f"Set fan speed success: {success}")
            except Exception as e:
                print(f"Error during control example: {e}")

    else:
        print("No NVIDIA GPUs found or NVML unavailable.")

    print("\n--- Cleanup ---")
    for monitor in monitors:
        try:
            monitor.cleanup()
        except Exception as e:
            print(f"Error cleaning up monitor {monitor.device_id}: {e}")
    for controller in controllers:
        try:
            controller.cleanup()
        except Exception as e:
            print(f"Error cleaning up controller {controller.device_id}: {e}")

    try:
        _shutdown_nvml_safe()
        print(f"Final NVML init count (should be 0): {_nvml_init_count}")
    except Exception as e:
        print(f"Error during final NVML shutdown check: {e}")