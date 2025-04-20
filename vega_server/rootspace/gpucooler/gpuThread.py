import globals
import copy
import time
import logging
from typing import Dict

# Use common utilities
from vega_common.utils.sliding_window import NumericSlidingWindow
from vega_common.utils.device_manager import DeviceManager
from vega_common.utils.gpu_devices import NvidiaGpuMonitor, NvidiaGpuController, NVMLError
from vega_common.utils.temperature_utils import gpu_temp_to_fan_speed

# Keep gpuDisplay for initial configuration, consider refactoring later
import gpucooler.gpu_configuration.gpuDisplay as gpuDisplay

# Import pynvml to check availability and count devices initially
try:
    import pynvml
except ImportError:
    pynvml = None
    logging.error("pynvml library not found. NVIDIA GPU monitoring/control disabled in gpuThread.")

TEMPERATURE_WINDOW_SIZE = 10

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def gpu_thread(_):
    """
    Monitors NVIDIA GPU temperature and controls fan speed using vega_common utilities.

    Args:
        _ : Unused argument (often used for thread target compatibility).

    Returns:
        None: This function runs indefinitely until an error or interruption.
    """
    device_manager = DeviceManager()
    gpu_temp_windows: Dict[str, NumericSlidingWindow] = {}
    gpu_controllers: Dict[str, NvidiaGpuController] = {}

    try:
        # Initial GPU configuration (consider moving this)
        try:
            logging.info("Configuring GPUs using gpuDisplay...")
            gpuDisplay.configure_gpus()
            logging.info("GPU configuration finished.")
        except Exception as e:
            logging.error(f"Failed during gpuDisplay.configure_gpus: {e}", exc_info=True)

        # Detect and register NVIDIA GPUs
        if pynvml:
            try:
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                logging.info(f"Found {device_count} NVIDIA GPU(s).")

                for i in range(device_count):
                    try:
                        monitor = NvidiaGpuMonitor(device_index=i, monitoring_interval=3.0)
                        controller = NvidiaGpuController(device_index=i)

                        device_manager.register_monitor(monitor)
                        device_manager.register_controller(controller)

                        gpu_temp_windows[monitor.device_id] = NumericSlidingWindow(
                            size=TEMPERATURE_WINDOW_SIZE
                        )
                        gpu_controllers[monitor.device_id] = (
                            controller  # Store controller for easy access
                        )

                        logging.info(
                            f"Registered monitor and controller for GPU {i} (ID: {monitor.device_id})"
                        )

                    except (NVMLError, ValueError) as e:
                        logging.error(
                            f"Failed to initialize monitor/controller for GPU {i}: {e}",
                            exc_info=True,
                        )

                pynvml.nvmlShutdown()  # Shutdown after initial count/setup

            except NVMLError as e:
                logging.error(f"Failed to initialize NVML for device detection: {e}", exc_info=True)
                # No GPUs will be monitored if NVML fails here
        else:
            logging.warning("pynvml not available. Skipping NVIDIA GPU detection.")

        if not device_manager.get_monitors_by_type("gpu"):
            logging.warning("No GPU monitors registered. GPU thread will idle.")
            # Keep thread alive but do nothing, or exit if appropriate
            while True:
                time.sleep(60)  # Sleep longer if no devices

        # Start monitoring
        device_manager.start_all_monitors()
        logging.info("GPU monitoring started.")

        # Main monitoring and control loop
        while True:
            all_statuses = device_manager.get_all_statuses()
            gpu_statuses = [s for s in all_statuses if s.device_type == "gpu"]

            for status in gpu_statuses:
                device_id = status.device_id

                # --- Temperature Reading and Averaging ---
                gpu_temp = status.get_property("temperature")

                if gpu_temp is None or status.is_error("temperature"):
                    logging.warning(
                        f"No valid temperature reading for GPU {device_id}. Skipping control."
                    )
                    continue  # Skip control logic if temp is invalid

                if device_id not in gpu_temp_windows:
                    # Should not happen if registration was successful, but handle defensively
                    logging.error(f"Temperature window not found for GPU {device_id}. Recreating.")
                    gpu_temp_windows[device_id] = NumericSlidingWindow(size=TEMPERATURE_WINDOW_SIZE)

                window = gpu_temp_windows[device_id]
                window.fill(gpu_temp)  # Fill window if it's new/empty
                window.add(gpu_temp)
                gpu_average_degree = window.get_average()

                # --- Fan Speed Calculation ---
                # Use the same modifiers as the original gpuTemp logic
                # O(1) complexity for each call
                speed_fan0 = gpu_temp_to_fan_speed(gpu_average_degree, modifier=0.001)
                speed_fan1 = gpu_temp_to_fan_speed(gpu_average_degree, modifier=0.05)

                # --- Fan Speed Control ---
                controller = gpu_controllers.get(device_id)
                if controller:
                    try:
                        # O(1) complexity for NVML call
                        success = controller.set_fan_speed(speed1=speed_fan0, speed2=speed_fan1)
                        if not success:
                            logging.warning(f"Failed to set fan speed for GPU {device_id}")
                    except Exception as e:
                        logging.error(
                            f"Error setting fan speed for GPU {device_id}: {e}", exc_info=True
                        )
                else:
                    logging.error(f"Controller not found for GPU {device_id}")

                # --- Logging and Global State Update ---
                # Retrieve current speeds from status for logging/globals
                current_fan1 = status.get_property("fan_speed_1")
                current_fan2 = status.get_property("fan_speed_2")

                logging.info(
                    f"GPU {device_id}: Temp={gpu_temp:.1f}°C, AvgTemp={gpu_average_degree:.1f}°C, "
                    f"Fan1 Cur={current_fan1}%, Set={speed_fan0}%, "
                    f"Fan2 Cur={current_fan2}%, Set={speed_fan1}%"
                )

                # Update global state (similar to previous logic)
                # Ensure keys match expected format if other parts rely on it
                gpu_index_str = device_id.split("_")[-1]  # Assuming ID format like 'nvidia_gpu_0'
                globals.WC_DATA_OUT[0][f"gpu{gpu_index_str}_degree"] = round(gpu_temp, 1)
                globals.WC_DATA_OUT[0][f"gpu{gpu_index_str}_average_degree"] = round(
                    gpu_average_degree, 1
                )
                globals.WC_DATA_OUT[0][f"gpu{gpu_index_str}_c_fan_speed1"] = current_fan1
                globals.WC_DATA_OUT[0][f"gpu{gpu_index_str}_c_fan_speed2"] = current_fan2
                globals.WC_DATA_OUT[0][f"gpu{gpu_index_str}_s_fan_speed1"] = speed_fan0
                globals.WC_DATA_OUT[0][f"gpu{gpu_index_str}_s_fan_speed2"] = speed_fan1
                # Add other properties if needed, e.g., name, utilization
                globals.WC_DATA_OUT[0][f"gpu{gpu_index_str}_name"] = status.device_name
                # globals.WC_DATA_OUT[0][f"gpu{gpu_index_str}_id"] = device_id # PCI ID

            # Wait before next cycle
            time.sleep(3)  # Keep the 3-second interval

    except KeyboardInterrupt:
        logging.info("GPU thread received KeyboardInterrupt. Shutting down.")
    except Exception as e:
        logging.error(f"Unhandled exception in GPU thread: {e}", exc_info=True)
    finally:
        logging.info("Stopping GPU monitors...")
        device_manager.stop_all_monitors()
        logging.info("GPU monitors stopped.")
        # NVML cleanup is handled within the Monitor/Controller cleanup methods via _shutdown_nvml_safe

    logging.info("GPU thread finished.")
    return None  # Explicitly return None
