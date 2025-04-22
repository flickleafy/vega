import globals
import time
import logging
from typing import Optional

# Use common utilities
from vega_common.utils.device_manager import DeviceManager
from vega_common.utils.cpu_devices import CpuMonitor, CpuController
from vega_common.utils.sliding_window import NumericSlidingWindow

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
TEMPERATURE_WINDOW_SIZE = 10  # Size of sliding window for temperature averaging
CPU_MONITOR_INTERVAL = 3.0  # How frequently to update CPU monitoring data (seconds)
DEFAULT_SLEEP_INTERVAL = 10  # Default sleep time when no recommendation is available (seconds)


def cpuclocking_thread(_):
    """
    Monitors CPU temperature and adjusts power plan (CPU governor) accordingly.

    Uses the DeviceManager with CpuMonitor and CpuController from vega_common utilities
    to implement intelligent CPU power management based on temperature and system load.

    Args:
        _ (Any): Unused argument (compatibility with thread target signature).

    Returns:
        None: This function runs indefinitely until an error or interruption.
    """
    logging.info("Initializing CPU clocking thread...")
    time.sleep(30)

    device_manager = DeviceManager()
    
    sleep_interval = DEFAULT_SLEEP_INTERVAL

    try:
        # Initialize CPU monitor and controller
        cpu_monitor = CpuMonitor(device_id="cpu_main", monitoring_interval=CPU_MONITOR_INTERVAL)
        cpu_controller = CpuController(device_id="cpu_main")

        # Register with device manager
        device_manager.register_monitor(cpu_monitor)
        device_manager.register_controller(cpu_controller)

        logging.info("Registered CPU monitor and controller")

        # Start monitoring
        device_manager.start_all_monitors()
        logging.info("CPU monitoring started")

        # Initial delay to allow first readings to come in
        time.sleep(5)

        # Main monitoring and control loop
        while True:
            # Get latest CPU status
            cpu_status = device_manager.get_device_status(device_id="cpu_main")

            if cpu_status:
                # Get current CPU temperature
                current_temp = cpu_status.get_property("temperature")

                # Update temperature window and calculate average
                if current_temp is not None:
                    # Get average temperature from sliding window
                    # TODO: replace to WC average temp
                    avg_temp = cpu_status.get_property_average("temperature")

                    # Get temperature trend
                    trend = cpu_status.get_property_trend("temperature")

                    # Log temperature info
                    logging.info(
                        f"CPU Temperature: Current={current_temp:.1f}°C, "
                        f"Average={avg_temp:.1f}°C, Trend={trend or 'unknown'}"
                    )

                    # Determine and apply optimal power plan with trend information
                    recommendation = cpu_controller.determine_optimal_power_plan(
                        avg_temp, trend=trend[1]
                    )
                    power_plan = recommendation["powerplan"]
                    sleep_interval = recommendation["sleep"]

                    # Apply power plan
                    success = cpu_controller.set_power_plan(power_plan)

                    # Update globals with power plan info
                    globals.WC_DATA_OUT[0]["cpu_powerplan"] = power_plan if success else "unknown"
                else:
                    logging.warning("CPU temperature reading not available")
                    # Use default sleep interval when temperature is unavailable
                    sleep_interval = DEFAULT_SLEEP_INTERVAL
            else:
                logging.warning("Failed to get CPU status from device manager")
                sleep_interval = DEFAULT_SLEEP_INTERVAL

            # Wait before next cycle (dynamic sleep based on recommendation)
            time.sleep(sleep_interval)

    except KeyboardInterrupt:
        logging.info("CPU clocking thread received KeyboardInterrupt. Shutting down.")
    except Exception as e:
        logging.error(f"Unhandled exception in CPU clocking thread: {e}", exc_info=True)
    finally:
        logging.info("Stopping CPU monitors...")
        device_manager.stop_all_monitors()
        logging.info("CPU monitors stopped.")

    logging.info("CPU clocking thread finished.")
    return None  # Explicitly return None
