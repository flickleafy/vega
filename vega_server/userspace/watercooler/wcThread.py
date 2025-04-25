import globals
import time
import logging
from typing import Dict, Optional, List, Tuple

# Common utilities
from vega_common.utils.temperature_utils import estimate_cpu_from_liquid_temp
from vega_common.utils.sliding_window import NumericSlidingWindow
from vega_common.utils.device_manager import DeviceManager
from vega_common.utils.cpu_devices import CpuMonitor  # Use the common CPU monitor
from vega_common.utils.watercooler_devices import WatercoolerMonitor, WatercoolerController  # New imports

VALUE_COLUMN = 1
LIQUID_TEMPERATURE_ROW = 0
FAN_SPEED_ROW = 1
PUMP_SPEED_ROW = 2
TEMPERATURE_WINDOW_SIZE = 10

# CPU monitoring constants
CPU_MONITOR_INTERVAL = 3.0

# Setup basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(threadName)s - %(message)s"
)


def watercooler_thread(_):
    """Monitor and control watercooler system and CPU temperature.

    This thread continuously monitors watercooling system metrics (liquid temperature,
    fan speed, pump speed) and CPU temperature using DeviceManager, and adjusts
    fan speeds and lighting based on temperature readings.

    Args:
        _ (int): Unused argument, maintained for thread function signature consistency.

    Returns:
        None: This thread runs continuously until an error or interruption.
    """
    logging.info("Initializing watercooler thread...")
    device_manager = DeviceManager()
    cpu_monitor_id = "cpu_main"  # Consistent ID for the CPU monitor

    # --- Initialize CPU Monitor ---
    try:
        # Create CPU monitor with explicit sensor preferences for better reliability
        # O(1) initialization complexity
        cpu_monitor = CpuMonitor(
            device_id=cpu_monitor_id, 
            monitoring_interval=CPU_MONITOR_INTERVAL,
        )

        if cpu_monitor.status.has_error("initialization"):
            logging.error(
                f"CPU Monitor initialization failed: {cpu_monitor.status.get_error('initialization')}"
            )
            cpu_monitor = None
        else:
            device_manager.register_monitor(cpu_monitor)
            logging.info(f"Registered CPU monitor (ID: {cpu_monitor_id})")

    except Exception as e:
        logging.error(f"Failed to create or register CPU monitor: {e}", exc_info=True)
        cpu_monitor = None

    # --- Initialize Watercooler Devices ---
    wc_monitors = []
    wc_controllers = []
    try:
        # Try to initialize watercooler devices using the common utilities
        # O(N) initialization complexity where N is the number of connected USB devices
        device_index = 0
        while True:
            try:
                # Device IDs should be unique, so we use index-based IDs
                wc_monitor_id = f"watercooler_{device_index}"
                wc_monitor = WatercoolerMonitor(
                    device_index=device_index,
                    monitoring_interval=3.0,  # Match the original thread's interval
                    device_id=wc_monitor_id
                )
                device_manager.register_monitor(wc_monitor)
                
                # Initialize the controller for this device
                wc_controller = WatercoolerController(
                    device_index=device_index,
                    device_id=wc_monitor_id
                )
                device_manager.register_controller(wc_controller)
                
                wc_monitors.append(wc_monitor)
                wc_controllers.append(wc_controller)
                
                logging.info(f"Initialized WC device {device_index}: {wc_monitor.device_name}")
                device_index += 1
            except IndexError:
                # No more devices available - this is expected
                break
            except Exception as e:
                # Skip this device if there's an issue
                logging.warning(f"Could not initialize watercooler device {device_index}: {e}")
                device_index += 1
                if device_index >= 5:  # Reasonable limit to avoid infinite loop
                    break

        if not wc_monitors:
            logging.warning("No compatible watercooling devices found.")
            if not cpu_monitor:
                logging.error("No CPU monitor and no watercooler devices. Exiting thread.")
                return None
            logging.warning("No watercooler devices, will only monitor CPU.")
        else:
            logging.info(f"Found {len(wc_monitors)} watercooling device(s).")

    except Exception as e:
        logging.error(f"Error during watercooler initialization: {e}", exc_info=True)
        wc_monitors = []
        wc_controllers = []
        if not cpu_monitor:
            logging.error("No CPU monitor and watercooler init failed. Exiting thread.")
            return None

    # --- Initialize Sliding Windows ---
    wc_temp_window = NumericSlidingWindow(capacity=TEMPERATURE_WINDOW_SIZE)
    

    try:
        if device_manager.get_monitors():
            device_manager.start_all_monitors()
            logging.info("Device monitoring started.")
        else:
            logging.info("No monitors registered to start.")

        # Allow a brief delay for monitors to collect initial data
        time.sleep(2)

        # --- Main Loop ---
        while True:
            cpu_temp = None
            cpu_average_temp = None
            cpu_temp_trend = None
            cpu_temp_rate = None
            
            # --- CPU Temperature Monitoring ---
            if cpu_monitor:
                # Get comprehensive CPU status information from DeviceManager
                # O(1) complexity for dictionary lookups
                cpu_status = device_manager.get_device_status(
                    device_type="cpu", device_id=cpu_monitor_id
                )
                
                if cpu_status:
                    # Get current temperature reading
                    # O(1) property access
                    cpu_temp = cpu_status.get_property("temperature")
                    
                    if cpu_temp is None or cpu_status.is_error("temperature"):
                        logging.warning(
                            f"CPU Monitor ({cpu_monitor_id}): No valid temperature reading. Will attempt estimation."
                        )
                        cpu_temp = None
                    else:
                        # Use the DeviceStatus built-in averages
                        # O(1) property access
                        cpu_average_temp = cpu_status.get_property_average("temperature")
                        
                        # Get temperature trend information
                        # O(1) property access
                        trend_info = cpu_status.get_property_trend("temperature")
                        if trend_info:
                            cpu_temp_rate, cpu_temp_trend = trend_info
                            logging.debug(
                                f"CPU temp trend: {cpu_temp_trend} at {cpu_temp_rate:.2f}°C/sample"
                            )
                        
                     
                else:
                    logging.warning(
                        f"Could not retrieve status for CPU monitor ({cpu_monitor_id})."
                    )

            # --- CPU-only Mode (No Watercooler Devices) ---
            if not wc_monitors:
                if cpu_temp is not None:
                    # If we have CPU temp but no watercooler, just log and store the values
                    trend_str = f", Trend: {cpu_temp_trend}" if cpu_temp_trend else ""
                    logging.info(
                        f"CPU Temp: {cpu_temp:.1f}°C, Avg: {cpu_average_temp:.1f}°C{trend_str} (No WC Devices)"
                    )
                    # Update global data structure with CPU temperature info
                    globals.WC_DATA_OUT[0]["cpu_degree"] = round(cpu_temp, 1)
                    globals.WC_DATA_OUT[0]["cpu_average_degree"] = round(cpu_average_temp, 1)
                    if cpu_temp_trend:
                        globals.WC_DATA_OUT[0]["cpu_temp_trend"] = cpu_temp_trend
                else:
                    logging.info("No CPU or WC devices active. Idling.")
                time.sleep(5)
                continue

            # --- Process Each Watercooler Device ---
            for index, wc_monitor in enumerate(wc_monitors):
                wc_controller = wc_controllers[index]

                wc_status = wc_monitor.get_status()
                if not wc_status:
                    logging.warning(
                        f"Could not get status for WC device {index} ({wc_monitor.device_name})"
                    )
                    continue

                # --- Extract Watercooler Metrics ---
                wc_temp = wc_status[LIQUID_TEMPERATURE_ROW][VALUE_COLUMN]
                wc_fan_speed = wc_status[FAN_SPEED_ROW][VALUE_COLUMN]
                wc_pump_speed = wc_status[PUMP_SPEED_ROW][VALUE_COLUMN]

                # --- CPU Temperature Estimation Fallback ---
                if cpu_temp is None:
                    # Fall back to estimating CPU temperature from liquid temperature
                    # if no sensor data is available
                    cpu_temp = estimate_cpu_from_liquid_temp(wc_temp)
                    logging.debug(
                        f"Estimated CPU temp: {cpu_temp:.1f}°C from liquid temp {wc_temp:.1f}°C"
                    )
                    
                    cpu_average_temp = cpu_temp
                    cpu_temp_trend = "estimated"

                # --- Watercooler Temperature Processing ---
                # Fill windows if they are empty (only happens on first iteration)
                # O(1) operations for small fixed-size window
                wc_temp_window.fill(wc_temp)

                # Add current temperatures to sliding windows
                # O(1) operations for small fixed-size window
                wc_temp_window.add(wc_temp)
                wc_average_temp = wc_temp_window.get_average()

                if cpu_average_temp is None:
                    cpu_average_temp = wc_average_temp

                # --- Control Logic ---
                # Weighted average of CPU and Liquid temperatures calculation
                # Used to smooth out the fan speed changes and avoid rapid fluctuations
                weighed_average_temp = (wc_average_temp + (cpu_average_temp * 0.85)) / 2

                try:
                    # Set LED color based on temperature - O(1) operation
                    array_color = wc_controller.set_led_color(wc_average_temp)
                    # Set fan speed based on temperature - O(1) operation
                    fan_status = wc_controller.set_fan_speed(weighed_average_temp)
                except Exception as e:
                    logging.error(
                        f"Error during WC control (LED/Fan) for device {index}: {e}", exc_info=True
                    )
                    array_color = [0, 0, 0]
                    fan_status = 0

                # --- Logging ---
                trend_str = f", CPU Trend: {cpu_temp_trend}" if cpu_temp_trend else ""
                logging.info(
                    f"Device {index}: Liquid Temp={wc_temp:.1f}°C (Avg={wc_average_temp:.1f}°C), "
                    f"CPU Temp={cpu_temp:.1f}°C (Avg={cpu_average_temp:.1f}°C){trend_str}, "
                    f"Weighted Avg={weighed_average_temp:.1f}°C, "
                    f"Fan Speed={wc_fan_speed} RPM (Set={fan_status}%), "
                    f"Pump Speed={wc_pump_speed} RPM, "
                    f"LED Color={array_color}"
                )

                # --- Update Global State ---
                globals.WC_DATA_OUT[0]["wc_degree"] = round(wc_temp, 1)
                globals.WC_DATA_OUT[0]["wc_average_degree"] = round(wc_average_temp, 1)
                globals.WC_DATA_OUT[0]["wc_fan_speed"] = wc_fan_speed
                globals.WC_DATA_OUT[0]["wc_fan_percent"] = fan_status
                globals.WC_DATA_OUT[0]["wc_pump_speed"] = wc_pump_speed
                globals.WC_DATA_OUT[0]["cpu_degree"] = round(cpu_temp, 1)
                globals.WC_DATA_OUT[0]["cpu_average_degree"] = (
                    round(cpu_average_temp, 1) if cpu_average_temp is not None else None
                )
                if cpu_temp_trend:
                    globals.WC_DATA_OUT[0]["cpu_temp_trend"] = cpu_temp_trend
                globals.WC_DATA_OUT[0]["array_color"] = array_color

                if len(wc_monitors) > 1:
                    time.sleep(0.5)

            time.sleep(3)

    except KeyboardInterrupt:
        logging.info("Watercooler thread received KeyboardInterrupt. Shutting down.")
    except Exception as e:
        logging.error(f"Unhandled exception in watercooler thread: {e}", exc_info=True)
    finally:
        logging.info("Stopping device monitors...")
        device_manager.stop_all_monitors()
        logging.info("Device monitors stopped.")

    logging.info("Watercooler thread finished.")
    return None
