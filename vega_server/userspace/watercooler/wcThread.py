import globals
import time
import logging
from typing import Dict

# Common utilities
from vega_common.utils.temperature_utils import estimate_cpu_from_liquid_temp
from vega_common.utils.sliding_window import NumericSlidingWindow
from vega_common.utils.device_manager import DeviceManager
from vega_common.utils.cpu_devices import CpuMonitor  # Use the common CPU monitor

# Watercooler specific modules
import watercooler.wcStatus as wcStatus
import lighting.lightingColor as lightingColor
import watercooler.wcTemp as wcTemp

VALUE_COLUMN = 1
LIQUID_TEMPERATURE_ROW = 0
FAN_SPEED_ROW = 1
PUMP_SPEED_ROW = 2
TEMPERATURE_WINDOW_SIZE = 10

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
        cpu_monitor = CpuMonitor(device_id=cpu_monitor_id, monitoring_interval=5.0)

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
    try:
        wc_devices = wcStatus.wc_initialize()
        if not wc_devices:
            logging.warning("No compatible watercooling devices found.")
            if not cpu_monitor:
                logging.error("No CPU monitor and no watercooler devices. Exiting thread.")
                return None
            logging.warning("No watercooler devices, will only monitor CPU.")
        else:
            logging.info(f"Found {len(wc_devices)} watercooling device(s).")

    except Exception as e:
        logging.error(f"Error during watercooler initialization: {e}", exc_info=True)
        wc_devices = []
        if not cpu_monitor:
            logging.error("No CPU monitor and watercooler init failed. Exiting thread.")
            return None

    # --- Initialize Sliding Windows ---
    wc_temp_window = NumericSlidingWindow(capacity=TEMPERATURE_WINDOW_SIZE)
    cpu_temp_window = NumericSlidingWindow(capacity=TEMPERATURE_WINDOW_SIZE)

    try:
        if device_manager.get_monitors():
            device_manager.start_all_monitors()
            logging.info("Device monitoring started.")
        else:
            logging.info("No monitors registered to start.")

        # --- Main Loop ---
        while True:
            cpu_temp = None
            cpu_average_temp = None
            if cpu_monitor:
                cpu_status = device_manager.get_device_status(
                    cpu_monitor.device_type, cpu_monitor_id
                )
                if cpu_status:
                    cpu_temp = cpu_status.get_property("temperature")
                    if cpu_temp is None or cpu_status.is_error("temperature"):
                        logging.warning(
                            f"CPU Monitor ({cpu_monitor_id}): No valid temperature reading. Will attempt estimation."
                        )
                        cpu_temp = None
                    else:
                        cpu_temp_window.fill(cpu_temp)
                        cpu_temp_window.add(cpu_temp)
                        cpu_average_temp = cpu_temp_window.get_average()
                else:
                    logging.warning(
                        f"Could not retrieve status for CPU monitor ({cpu_monitor_id})."
                    )

            if not wc_devices:
                if cpu_temp is not None:
                    logging.info(
                        f"CPU Temp: {cpu_temp:.1f}°C, Avg: {cpu_average_temp:.1f}°C (No WC Devices)"
                    )
                    globals.WC_DATA_OUT[0]["cpu_degree"] = round(cpu_temp, 1)
                    globals.WC_DATA_OUT[0]["cpu_average_degree"] = round(cpu_average_temp, 1)
                else:
                    logging.info("No CPU or WC devices active. Idling.")
                time.sleep(5)
                continue

            for index, device in enumerate(wc_devices):
                if "LED" in device.description:
                    continue

                wc_status = wcStatus.get_wc_status(wc_devices, index)
                if not wc_status:
                    logging.warning(
                        f"Could not get status for WC device {index} ({device.description})"
                    )
                    continue

                wc_temp = wc_status[LIQUID_TEMPERATURE_ROW][VALUE_COLUMN]
                wc_fan_speed = wc_status[FAN_SPEED_ROW][VALUE_COLUMN]
                wc_pump_speed = wc_status[PUMP_SPEED_ROW][VALUE_COLUMN]

                if cpu_temp is None:
                    # Fall back to estimating CPU temperature from liquid temperature
                    # if no sensor data is available
                    cpu_temp = estimate_cpu_from_liquid_temp(wc_temp)
                    logging.debug(
                        f"Estimated CPU temp: {cpu_temp:.1f}°C from liquid temp {wc_temp:.1f}°C"
                    )
                    cpu_temp_window.fill(cpu_temp)
                    cpu_temp_window.add(cpu_temp)
                    cpu_average_temp = cpu_temp_window.get_average()

                # Fill windows if they are empty (only happens on first iteration)
                wc_temp_window.fill(wc_temp)

                # Add current temperatures to sliding windows
                wc_temp_window.add(wc_temp)
                wc_average_temp = wc_temp_window.get_average()

                if cpu_average_temp is None:
                    cpu_average_temp = wc_average_temp

                # Weighted average of CPU and Liquid temperatures calculation
                # Used to smooth out the fan speed changes and avoid rapid fluctuations
                weighed_average_temp = (wc_average_temp + (cpu_average_temp * 0.85)) / 2

                try:
                    array_color = lightingColor.set_led_color(wc_devices, index, wc_average_temp)
                    fan_status = wcTemp.set_wc_fan_speed(wc_devices, index, weighed_average_temp)
                except Exception as e:
                    logging.error(
                        f"Error during WC control (LED/Fan) for device {index}: {e}", exc_info=True
                    )
                    array_color = [0, 0, 0]
                    fan_status = 0

                logging.info(
                    f"Device {index}: Liquid Temp={wc_temp:.1f}°C (Avg={wc_average_temp:.1f}°C), "
                    f"CPU Temp={cpu_temp:.1f}°C (Avg={cpu_average_temp:.1f}°C), "
                    f"Weighted Avg={weighed_average_temp:.1f}°C, "
                    f"Fan Speed={wc_fan_speed} RPM (Set={fan_status}%), "
                    f"Pump Speed={wc_pump_speed} RPM, "
                    f"LED Color={array_color}"
                )

                globals.WC_DATA_OUT[0]["wc_degree"] = round(wc_temp, 1)
                globals.WC_DATA_OUT[0]["wc_average_degree"] = round(wc_average_temp, 1)
                globals.WC_DATA_OUT[0]["wc_fan_speed"] = wc_fan_speed
                globals.WC_DATA_OUT[0]["wc_fan_percent"] = fan_status
                globals.WC_DATA_OUT[0]["wc_pump_speed"] = wc_pump_speed
                globals.WC_DATA_OUT[0]["cpu_degree"] = round(cpu_temp, 1)
                globals.WC_DATA_OUT[0]["cpu_average_degree"] = (
                    round(cpu_average_temp, 1) if cpu_average_temp is not None else None
                )
                globals.WC_DATA_OUT[0]["array_color"] = array_color

                if len(wc_devices) > 1:
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
