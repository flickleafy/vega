"""
Concrete implementations for monitoring and controlling NVIDIA GPUs using NVML.
"""

import threading
import time  # Added for example usage
from typing import Optional, Tuple, List, Dict, Any, Union

from .device_monitor import DeviceMonitor
from .device_controller import DeviceController
from .device_status import DeviceStatus
from .logging_utils import get_module_logger

# Setup module-specific logging (must be before any logger usage)
logger = get_module_logger("vega_common/utils/gpu_devices")

# Import pynvml from the installed package, not the removed vendored copy
try:
    import pynvml
except ImportError:
    pynvml = None  # Allow graceful failure if NVML is not installed/available
    logger.error("pynvml library not found. NVIDIA GPU monitoring/control disabled.")

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
                logger.debug("NVML initialized.")
            except Exception as error:
                if hasattr(pynvml, "NVMLError") and isinstance(error, pynvml.NVMLError):
                    logger.error(f"Failed to initialize NVML: {str(error)}")
                    raise NVMLError(f"Failed to initialize NVML: {str(error)}") from error
                else:
                    logger.error(f"Unexpected error initializing NVML: {str(error)}")
                    raise NVMLError(f"Failed to initialize NVML: {str(error)}") from error
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
                logger.debug("NVML shut down.")
            except Exception as error:
                # Log error but don't raise, as shutdown failure is less critical
                logger.error(f"Failed to shut down NVML: {str(error)}")


def decode_string(byte_string: Union[bytes, str]) -> str:
    """
    Decode a byte string to a UTF-8 string, handling NVML-specific encoding.

    Args:
        byte_string (Union[bytes, str]): The byte string to decode.

    Returns:
        str: The decoded string.

    Time complexity: O(n) where n is the length of the string.
    """
    if isinstance(byte_string, bytes):
        return byte_string.decode("utf-8")
    elif isinstance(byte_string, str):
        return byte_string
    else:
        return str(byte_string)


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

        # First check if the device index is valid before doing anything else
        try:
            device_count = pynvml.nvmlDeviceGetCount()
            if not (0 <= device_index < device_count):
                _shutdown_nvml_safe()  # Clean up before raising
                logger.error(f"Invalid GPU index {device_index}: Found {device_count} devices.")
                # This exception should not be caught by the later exception handlers
                raise ValueError(
                    f"Invalid device_index {device_index}. Found {device_count} devices."
                )
        except Exception as error:
            # Only catch NVML errors here, not the ValueError we might have raised above
            if not isinstance(error, ValueError):
                _shutdown_nvml_safe()
                logger.error(f"Failed to get device count: {str(error)}")
                raise NVMLError(f"Failed to get device count: {str(error)}") from error
            raise  # Re-raise ValueError

        # Only proceed to get handle if device index is valid
        try:
            self.handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_index)

            # Try to get PCI bus ID if available - handle gracefully if not
            try:
                pci_info = pynvml.nvmlDeviceGetPciInfo(self.handle)
                # Format busId to be filesystem/URL safe if needed, but keep original for display
                if hasattr(pci_info, "busId"):
                    device_id = decode_string(pci_info.busId)
            except Exception as pci_error:
                logger.warning(
                    f"Failed to get PCI info for GPU {device_index}: {str(pci_error)}. Using default device ID."
                )
                # Continue with default device_id

            # Try to get device name if available - handle gracefully if not
            try:
                name_bytes = pynvml.nvmlDeviceGetName(self.handle)
                if name_bytes is not None:  # Check if name is available
                    device_name = decode_string(name_bytes)
            except Exception as name_error:
                logger.warning(
                    f"Failed to get device name for GPU {device_index}: {str(name_error)}. Using default name."
                )
                # Continue with default device_name

        except Exception as error:
            _shutdown_nvml_safe()  # Decrement count if init succeeded but handle failed
            logger.error(f"Failed to get handle for GPU {device_index}: {str(error)}")
            raise NVMLError(f"Failed to get handle for GPU {device_index}: {str(error)}") from error

        super().__init__(
            device_id=device_id,
            device_type="gpu",
            device_name=device_name,
            monitoring_interval=monitoring_interval,
            tracked_properties=[
                "temperature",
                "fan_speed_1",
                "fan_speed_2",
                "gpu_utilization",
                "memory_utilization",
            ],
        )
        logger.info(f"Initialized monitor for {device_name} (ID: {device_id})")

    def update_status(self):
        """
        Update GPU status with fresh data from NVML.

        Complexity: O(1) for NVML calls.
        """
        if self.handle is None:
            logger.warning(f"Skipping update for GPU {self.device_id}: NVML handle not available.")
            return

        try:
            # --- Temperature ---
            try:
                temp = pynvml.nvmlDeviceGetTemperature(self.handle, pynvml.NVML_TEMPERATURE_GPU)
                self.status.update_property("temperature", temp)
            except Exception as e:
                # Check if the error is 'NOT_SUPPORTED'
                if (
                    hasattr(pynvml, "NVMLError")
                    and isinstance(e, pynvml.NVMLError)
                    and hasattr(pynvml, "NVML_ERROR_NOT_SUPPORTED")
                    and e.args[0] == pynvml.NVML_ERROR_NOT_SUPPORTED
                ):
                    logger.debug(f"Temperature sensor not supported for {self.device_id}.")
                    self.status.update_property(
                        "temperature", None, is_error=False
                    )  # Mark as None, not error
                elif isinstance(e, pynvml.NVMLError):
                    # NVML specific errors can be warnings
                    logger.warning(f"Could not get temperature for {self.device_id}: {e}")
                    self.status.update_property("temperature", None, is_error=True)
                else:
                    # General exceptions (like RuntimeError) should be logged as errors
                    logger.error(f"Unexpected error getting temperature for {self.device_id}: {e}")
                    self.status.update_property("temperature", None, is_error=True)

            # --- Fan Speed ---
            try:
                num_fans = pynvml.nvmlDeviceGetNumFans(self.handle)
                fan1 = None
                fan2 = None

                # If the GPU has no fans at all, mark both fan speeds as None but not errors
                if num_fans == 0:
                    logger.debug(f"No fans detected for {self.device_id}.")
                    self.status.update_property("fan_speed_1", None, is_error=False)
                    self.status.update_property("fan_speed_2", None, is_error=False)
                else:
                    # GPU has at least one fan
                    if num_fans >= 1:
                        try:
                            fan1 = pynvml.nvmlDeviceGetFanSpeed_v2(self.handle, 0)
                        except Exception as e_fan1:
                            if (
                                hasattr(pynvml, "NVMLError")
                                and isinstance(e_fan1, pynvml.NVMLError)
                                and hasattr(pynvml, "NVML_ERROR_NOT_SUPPORTED")
                                and e_fan1.args[0] == pynvml.NVML_ERROR_NOT_SUPPORTED
                            ):
                                logger.debug(f"Fan 0 speed not supported for {self.device_id}.")
                                # Explicitly mark as not an error when feature is not supported
                                self.status.update_property("fan_speed_1", None, is_error=False)
                            elif isinstance(e_fan1, pynvml.NVMLError):
                                logger.warning(
                                    f"Failed to get fan 0 speed for {self.device_id}: {e_fan1}"
                                )
                                self.status.update_property("fan_speed_1", None, is_error=True)
                            else:
                                logger.error(
                                    f"Unexpected error getting fan 0 speed for {self.device_id}: {e_fan1}"
                                )
                                self.status.update_property("fan_speed_1", None, is_error=True)
                        else:
                            # Update fan property if no exception occurred
                            self.status.update_property("fan_speed_1", fan1)

                    if num_fans >= 2:
                        try:
                            fan2 = pynvml.nvmlDeviceGetFanSpeed_v2(self.handle, 1)
                        except Exception as e_fan2:
                            if (
                                hasattr(pynvml, "NVMLError")
                                and isinstance(e_fan2, pynvml.NVMLError)
                                and hasattr(pynvml, "NVML_ERROR_NOT_SUPPORTED")
                                and e_fan2.args[0] == pynvml.NVML_ERROR_NOT_SUPPORTED
                            ):
                                logger.debug(f"Fan 1 speed not supported for {self.device_id}.")
                                # Explicitly mark as not an error when feature is not supported
                                self.status.update_property("fan_speed_2", None, is_error=False)
                            elif isinstance(e_fan2, pynvml.NVMLError):
                                logger.warning(
                                    f"Failed to get fan 1 speed for {self.device_id}: {e_fan2}"
                                )
                                self.status.update_property("fan_speed_2", None, is_error=True)
                            else:
                                logger.error(
                                    f"Unexpected error getting fan 1 speed for {self.device_id}: {e_fan2}"
                                )
                                self.status.update_property("fan_speed_2", None, is_error=True)
                        else:
                            # Update fan property if no exception occurred
                            self.status.update_property("fan_speed_2", fan2)
                    else:
                        # If we have fewer than 2 fans, mark fan_speed_2 as None but not an error
                        self.status.update_property("fan_speed_2", None, is_error=False)

                    # Handle fan_speed_1 if no fans at all (this case shouldn't actually
                    # happen with the new structure)
                    if num_fans < 1:
                        self.status.update_property("fan_speed_1", None, is_error=False)

            except Exception as e:
                if isinstance(e, pynvml.NVMLError):
                    logger.warning(f"Could not get fan speed for {self.device_id}: {e}")
                else:
                    logger.error(f"Unexpected error getting fan speed for {self.device_id}: {e}")
                self.status.update_property("fan_speed_1", None, is_error=True)
                self.status.update_property("fan_speed_2", None, is_error=True)

            # --- Utilization ---
            try:
                util = pynvml.nvmlDeviceGetUtilizationRates(self.handle)
                self.status.update_property("gpu_utilization", util.gpu)
                self.status.update_property("memory_utilization", util.memory)
            except Exception as e:
                if (
                    hasattr(pynvml, "NVMLError")
                    and isinstance(e, pynvml.NVMLError)
                    and hasattr(pynvml, "NVML_ERROR_NOT_SUPPORTED")
                    and e.args[0] == pynvml.NVML_ERROR_NOT_SUPPORTED
                ):
                    logger.debug(f"Utilization rates not supported for {self.device_id}.")
                    self.status.update_property("gpu_utilization", None, is_error=False)
                    self.status.update_property("memory_utilization", None, is_error=False)
                elif isinstance(e, pynvml.NVMLError):
                    logger.warning(f"Could not get utilization for {self.device_id}: {e}")
                    self.status.update_property("gpu_utilization", None, is_error=True)
                    self.status.update_property("memory_utilization", None, is_error=True)
                else:
                    logger.error(f"Unexpected error getting utilization for {self.device_id}: {e}")
                    self.status.update_property("gpu_utilization", None, is_error=True)
                    self.status.update_property("memory_utilization", None, is_error=True)

            # Mark status as updated successfully
            self.status.mark_updated()

        except Exception as e:
            logger.error(f"NVML error during update for {self.device_id}: {e}")
            # Mark all properties as error state if a general NVML error occurs
            for prop in self.tracked_properties:
                self.status.update_property(prop, None, is_error=True)
            self.status.mark_updated()  # Mark update attempt even if failed

    def cleanup(self):
        """Release NVML resources."""
        # Complexity: O(1)
        _shutdown_nvml_safe()
        logger.info(f"Cleaned up monitor for {self.device_id}")


# Set GPU fan speed %
# nvidia-settings -a [gpu:0]/GPUFanControlState=1 -a [fan:0]/GPUTargetFanSpeed=20


class NvidiaGpuController(DeviceController):
    """
    Controller for NVIDIA GPUs using the NVML library.

    Provides methods to set fan speeds and power limits for thermal management.
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
                _shutdown_nvml_safe()  # Make sure to clean up before raising
                logger.error(f"Invalid GPU index {device_index}: Found {device_count} devices.")
                raise ValueError(
                    f"Invalid device_index {device_index}. Found {device_count} devices."
                )

            self.handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_index)
            pci_info = pynvml.nvmlDeviceGetPciInfo(self.handle)
            device_id = decode_string(pci_info.busId)
            device_name = decode_string(pynvml.nvmlDeviceGetName(self.handle))

        except pynvml.NVMLError as error:
            _shutdown_nvml_safe()
            logger.error(f"Failed to get handle for GPU controller {device_index}: {str(error)}")
            raise NVMLError(
                f"Failed to get handle for GPU controller {device_index}: {str(error)}"
            ) from error
        except ValueError as error:
            # This is now only needed for any other ValueError that might be raised elsewhere,
            # since we're directly raising the device_index validation error above
            _shutdown_nvml_safe()
            logger.error(f"Invalid GPU index {device_index}: {str(error)}")
            raise error

        super().__init__(device_id=device_id, device_type="gpu", device_name=device_name)
        logger.info(f"Initialized controller for {self.device_name} (ID: {self.device_id})")

    def set_fan_speed(self, *fan_speeds: int) -> bool:
        """
        Set the speed for the GPU fans.

        Args:
            *fan_speeds (int): Target speed percentages for each fan.
                - If one speed is provided, it is used for all fans.
                - If multiple speeds are provided, each is applied to the corresponding fan.
                - Unspecified fans default to the first speed value.

        Returns:
            bool: True if successful, False otherwise.

        Complexity: O(n) where n is the number of fans.
        """
        if self.handle is None:
            logger.error(f"Cannot set fan speed for {self.device_id}: NVML handle not available.")
            return False

        if not fan_speeds:
            logger.error(f"Cannot set fan speed for {self.device_id}: No speed values provided.")
            return False

        success = True
        try:
            num_fans = pynvml.nvmlDeviceGetNumFans(self.handle)

            if num_fans == 0:
                logger.debug(f"No fans detected for {self.device_id}.")
                return True  # Nothing to set, not a failure

            # Build list of speeds for each fan, defaulting to first speed if not specified
            default_speed = max(0, min(100, fan_speeds[0]))
            speeds = []
            for i in range(num_fans):
                if i < len(fan_speeds):
                    speeds.append(max(0, min(100, fan_speeds[i])))
                else:
                    speeds.append(default_speed)

            # Set speed for each fan
            for fan_index, speed in enumerate(speeds):
                try:
                    pynvml.nvmlDeviceSetFanSpeed_v2(self.handle, fan_index, speed)
                    logger.debug(f"Set {self.device_id} Fan {fan_index} speed to {speed}%")
                except pynvml.NVMLError as error:
                    # Some cards report fans but don't allow setting speed
                    if (
                        hasattr(pynvml, "NVML_ERROR_NOT_SUPPORTED")
                        and isinstance(error, pynvml.NVMLError)
                        and error.args[0] == pynvml.NVML_ERROR_NOT_SUPPORTED
                    ):
                        logger.warning(
                            f"Fan {fan_index} speed control not supported for {self.device_id}."
                        )
                        # Don't mark as failure if control is just not supported
                    else:
                        logger.warning(
                            f"Failed to set fan {fan_index} speed for {self.device_id}: {str(error)}"
                        )
                        success = False  # Mark as partially failed if one fan fails

        except pynvml.NVMLError as error:
            logger.error(f"NVML error setting fan speed for {self.device_id}: {str(error)}")
            success = False

        return success

    def apply_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Apply specified settings to the GPU.

        Args:
            settings (Dict[str, Any]): Dictionary of settings to apply.
                Supported keys:
                - 'fan_speed': int or tuple of two ints for fan speed percentages

        Returns:
            bool: True if all settings were applied successfully, False otherwise.

        Complexity: O(1) for each setting applied.
        """
        if self.handle is None:
            logger.error(f"Cannot apply settings for {self.device_id}: NVML handle not available.")
            return False

        success = True
        applied_any = False

        if "fan_speed" in settings:
            fan_speed = settings["fan_speed"]
            if isinstance(fan_speed, (int, float)):
                # Single value for all fans
                fan_result = self.set_fan_speed(int(fan_speed))
                success = success and fan_result
                applied_any = True
            elif isinstance(fan_speed, (list, tuple)) and len(fan_speed) >= 1:
                # Different values for each fan (supports any number of fans)
                fan_result = self.set_fan_speed(*[int(s) for s in fan_speed])
                success = success and fan_result
                applied_any = True
            else:
                logger.error(
                    f"{self.device_id}: Invalid fan_speed format. Expected int or list/tuple of ints."
                )
                success = False

        # Add more settings handlers here as needed

        # Return False if no settings were recognized/applied
        return success if applied_any else False

    def get_available_settings(self) -> Dict[str, Any]:
        """
        Get available controllable settings and their current values.

        Returns:
            Dict[str, Any]: Dictionary of available settings.

        Complexity: O(1) for NVML calls.
        """
        settings = {
            "device_name": self.device_name,
            "device_id": self.device_id,
            "controllable_settings": ["fan_speed"],
        }

        # Get current fan speeds if possible
        if self.handle is not None:
            try:
                num_fans = pynvml.nvmlDeviceGetNumFans(self.handle)
                fan_speeds = []

                for i in range(num_fans):
                    try:
                        speed = pynvml.nvmlDeviceGetFanSpeed_v2(self.handle, i)
                        fan_speeds.append(speed)
                    except pynvml.NVMLError:
                        fan_speeds.append(None)

                settings["current_fan_speeds"] = fan_speeds
                settings["num_fans"] = num_fans
            except pynvml.NVMLError as error:
                logger.debug(f"Could not get fan information for {self.device_id}: {str(error)}")
                settings["current_fan_speeds"] = []
                settings["num_fans"] = 0

        return settings

    def get_power_limits(self) -> Dict[str, float]:
        """
        Get current, minimum, and maximum power limits in watts.
        
        Returns:
            Dict with 'current_watts', 'min_watts', 'max_watts', 'default_watts' keys.
            Empty dict if power management is not supported.
            
        Complexity: O(1) for NVML calls.
        """
        if self.handle is None:
            logger.error(f"Cannot get power limits for {self.device_id}: NVML handle not available.")
            return {}
        
        try:
            # NVML returns power values in milliwatts
            current_mw = pynvml.nvmlDeviceGetPowerManagementLimit(self.handle)
            default_mw = pynvml.nvmlDeviceGetPowerManagementDefaultLimit(self.handle)
            min_mw, max_mw = pynvml.nvmlDeviceGetPowerManagementLimitConstraints(self.handle)
            
            return {
                "current_watts": current_mw / 1000.0,
                "min_watts": min_mw / 1000.0,
                "max_watts": max_mw / 1000.0,
                "default_watts": default_mw / 1000.0,
            }
        except pynvml.NVMLError as e:
            if (
                hasattr(pynvml, "NVML_ERROR_NOT_SUPPORTED")
                and e.args[0] == pynvml.NVML_ERROR_NOT_SUPPORTED
            ):
                logger.debug(f"Power management not supported for {self.device_id}")
            else:
                logger.warning(f"Failed to get power limits for {self.device_id}: {e}")
            return {}
    
    def set_power_limit(self, watts: float) -> bool:
        """
        Set GPU power limit in watts.
        
        Note: This typically requires root privileges.
        
        Args:
            watts: Target power limit in watts. Will be clamped to valid range.
            
        Returns:
            bool: True if successful, False otherwise.
            
        Complexity: O(1) for NVML calls.
        """
        if self.handle is None:
            logger.error(f"Cannot set power limit for {self.device_id}: NVML handle not available.")
            return False
        
        try:
            limits = self.get_power_limits()
            if not limits:
                logger.warning(f"Cannot set power limit for {self.device_id}: limits not available")
                return False
            
            # Clamp to valid range
            min_watts = limits["min_watts"]
            max_watts = limits["max_watts"]
            clamped = max(min_watts, min(watts, max_watts))
            
            if clamped != watts:
                logger.info(
                    f"Clamped power limit from {watts:.1f}W to {clamped:.1f}W "
                    f"(range: {min_watts:.1f}W - {max_watts:.1f}W)"
                )
            
            # NVML expects milliwatts
            pynvml.nvmlDeviceSetPowerManagementLimit(self.handle, int(clamped * 1000))
            logger.info(f"Set {self.device_id} power limit to {clamped:.1f}W")
            return True
            
        except pynvml.NVMLError as e:
            if (
                hasattr(pynvml, "NVML_ERROR_NOT_SUPPORTED")
                and e.args[0] == pynvml.NVML_ERROR_NOT_SUPPORTED
            ):
                logger.warning(f"Power limit control not supported for {self.device_id}")
            elif (
                hasattr(pynvml, "NVML_ERROR_NO_PERMISSION")
                and e.args[0] == pynvml.NVML_ERROR_NO_PERMISSION
            ):
                logger.warning(
                    f"Permission denied setting power limit for {self.device_id}. "
                    "Root privileges required."
                )
            else:
                logger.error(f"Failed to set power limit for {self.device_id}: {e}")
            return False
    
    def reset_power_limit(self) -> bool:
        """
        Reset power limit to the default value.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        limits = self.get_power_limits()
        if limits and "default_watts" in limits:
            return self.set_power_limit(limits["default_watts"])
        return False
    
    def apply_thermal_protection(
        self, 
        temperature: float, 
        tjmax: float = 83.0
    ) -> Optional[float]:
        """
        Reduce power limit if GPU is approaching thermal limit.
        
        This provides graduated power reduction based on how close the GPU
        is to its thermal limit, helping to prevent thermal throttling.
        
        Args:
            temperature: Current GPU temperature in °C.
            tjmax: Maximum safe junction temperature (default 83°C for most NVIDIA GPUs).
            
        Returns:
            The new power limit in watts if changed, None if unchanged or failed.
            
        Complexity: O(1) for NVML calls.
        """
        limits = self.get_power_limits()
        if not limits:
            logger.debug(f"Cannot apply thermal protection for {self.device_id}: limits not available")
            return None
        
        max_watts = limits["max_watts"]
        current_watts = limits["current_watts"]
        
        # Calculate power reduction based on proximity to tjmax
        temp_ratio = temperature / tjmax
        
        if temp_ratio >= 0.95:  # Critical: 95%+ of tjmax
            target_percent = 0.60  # Reduce to 60% of max
            logger.warning(
                f"{self.device_id}: Critical temp {temperature:.1f}°C "
                f"({temp_ratio*100:.0f}% of tjmax), reducing power to 60%"
            )
        elif temp_ratio >= 0.90:  # Hot: 90-95% of tjmax
            target_percent = 0.75  # Reduce to 75% of max
            logger.info(
                f"{self.device_id}: Hot temp {temperature:.1f}°C "
                f"({temp_ratio*100:.0f}% of tjmax), reducing power to 75%"
            )
        elif temp_ratio >= 0.85:  # Warm: 85-90% of tjmax
            target_percent = 0.90  # Reduce to 90% of max
            logger.debug(
                f"{self.device_id}: Warm temp {temperature:.1f}°C "
                f"({temp_ratio*100:.0f}% of tjmax), reducing power to 90%"
            )
        else:  # Cool: below 85% of tjmax
            target_percent = 1.0  # Restore to max
            if current_watts < max_watts * 0.99:  # Only log if actually restoring
                logger.info(
                    f"{self.device_id}: Cool temp {temperature:.1f}°C, "
                    f"restoring power to 100%"
                )
        
        target_watts = max_watts * target_percent
        
        # Only change if significantly different (> 5W difference)
        if abs(current_watts - target_watts) > 5:
            if self.set_power_limit(target_watts):
                return target_watts
        
        return None

    def cleanup(self):
        """Release NVML resources."""
        # Complexity: O(1)
        _shutdown_nvml_safe()
        logger.info(f"Cleaned up controller for {self.device_id}")


# Example usage (for testing purposes, would normally be used by DeviceManager)
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.DEBUG)
#     monitors: List[NvidiaGpuMonitor] = []
#     controllers: List[NvidiaGpuController] = []
#     gpu_count = 0
#     try:
#         _initialize_nvml_safe()  # Initial check
#         gpu_count = pynvml.nvmlDeviceGetCount()
#         _shutdown_nvml_safe()  # Close initial check
#         print(f"Found {gpu_count} NVIDIA GPUs.")

#     except NVMLError as e:
#         print(f"NVML Error during detection: {e}")
#         gpu_count = 0  # Ensure count is 0 if detection fails

#     if gpu_count > 0:
#         for i in range(gpu_count):
#             try:
#                 monitor = NvidiaGpuMonitor(device_index=i, monitoring_interval=1.0)
#                 monitors.append(monitor)
#                 controller = NvidiaGpuController(device_index=i)
#                 controllers.append(controller)
#             except (NVMLError, ValueError) as e:
#                 print(f"Could not initialize monitor/controller for GPU {i}: {e}")

#         if monitors:
#             print("\n--- Monitoring (Example: First GPU) ---")
#             try:
#                 monitors[0].update_status()
#                 status_dict = monitors[0].status.get_all_properties()
#                 print(f"GPU {monitors[0].device_id} Status:")
#                 for key, value in status_dict.items():
#                     print(f"  {key}: {value}")

#             except Exception as e:
#                 print(f"Error during monitoring example: {e}")

#         if controllers:
#             print("\n--- Controlling (Example: First GPU) ---")
#             try:
#                 print("Attempting to set fan speed to 50% for GPU 0 (Fan 0 and 1)")
#                 success = controllers[0].set_fan_speed(50)
#                 print(f"Set fan speed success: {success}")
#             except Exception as e:
#                 print(f"Error during control example: {e}")

#     else:
#         print("No NVIDIA GPUs found or NVML unavailable.")

#     print("\n--- Cleanup ---")
#     for monitor in monitors:
#         try:
#             monitor.cleanup()
#         except Exception as e:
#             print(f"Error cleaning up monitor {monitor.device_id}: {e}")
#     for controller in controllers:
#         try:
#             controller.cleanup()
#         except Exception as e:
#             print(f"Error cleaning up controller {controller.device_id}: {e}")

#     try:
#         _shutdown_nvml_safe()
#         print(f"Final NVML init count (should be 0): {_nvml_init_count}")
#     except Exception as e:
#         print(f"Error during final NVML shutdown check: {e}")
