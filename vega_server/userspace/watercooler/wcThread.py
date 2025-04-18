import globals
import time
from vega_common.utils.temperature_utils import estimate_cpu_from_liquid_temp
from vega_common.utils.sliding_window import NumericSlidingWindow
import watercooler.wcStatus as wcStatus
import watercooler.cpuStatus as cpuStatus
import lighting.lightingColor as lightingColor
import watercooler.wcTemp as wcTemp

VALUE_COLUMN = 1
LIQUID_TEMPERATURE_ROW = 0
FAN_SPEED_ROW = 1
PUMP_SPEED_ROW = 2
TEMPERATURE_WINDOW_SIZE = 10

def watercooler_thread(_):
    """Monitor and control watercooler system.
    
    This thread continuously monitors watercooling system metrics (liquid temperature,
    fan speed, pump speed) and CPU temperature, and adjusts fan speeds and lighting
    based on temperature readings.

    Args:
        _ (int): Unused argument, maintained for thread function signature consistency.

    Raises:
        SystemExit: If no compatible watercooling devices are found.

    Returns:
        None: This thread runs continuously.
    """
    wc_temp_window = NumericSlidingWindow(size=TEMPERATURE_WINDOW_SIZE)
    cpu_temp_window = NumericSlidingWindow(size=TEMPERATURE_WINDOW_SIZE)
    devices = wcStatus.wc_initialize()
    
    if len(devices) > 0:
        while True:
            for index, device in enumerate(devices):
                print(f"Found device: {device.description}")
                if "LED" in device.description:
                    continue
                wc_status = wcStatus.get_wc_status(devices, index)
                
                wc_temp = wc_status[LIQUID_TEMPERATURE_ROW][VALUE_COLUMN]
                wc_fan_speed = wc_status[FAN_SPEED_ROW][VALUE_COLUMN]
                wc_pump_speed = wc_status[PUMP_SPEED_ROW][VALUE_COLUMN]
                cpu_temp = cpuStatus.get_cpu_status()

                if cpu_temp == 0:
                    # Use common temperature utility instead
                    cpu_temp = estimate_cpu_from_liquid_temp(wc_temp)

                # Fill windows if they are empty (only happens on first iteration)
                wc_temp_window.fill(wc_temp)
                cpu_temp_window.fill(cpu_temp)

                # Add current temperatures to sliding windows
                wc_temp_window.add(wc_temp)
                cpu_temp_window.add(cpu_temp)

                wc_average_temp = wc_temp_window.get_average()
                cpu_average_temp = cpu_temp_window.get_average()
                weighed_average_temp = (
                    wc_average_temp + (cpu_average_temp * 0.85)) / 2

                array_color = lightingColor.set_led_color(
                    devices, index, wc_average_temp)
                fan_status = wcTemp.set_wc_fan_speed(
                    devices, index, weighed_average_temp)

                print("Liquid temp ", wc_temp)
                print("CPU temp", cpu_temp)
                print("Average liquid temps", wc_average_temp)
                print("Average cpu temps", cpu_average_temp)
                print("Weighed Average temps", weighed_average_temp)
                print("Fans speed ", wc_fan_speed)
                print("Pump speed ", wc_pump_speed)
                print("RGB color set to " + str(array_color))
                print("Fan speed set to " + str(fan_status) + " per cent")
                print("\n")

                globals.WC_DATA_OUT[0]["wc_degree"] = round(wc_temp, 1)
                globals.WC_DATA_OUT[0]["wc_average_degree"] = round(
                    wc_average_temp, 1)
                globals.WC_DATA_OUT[0]["wc_fan_speed"] = wc_fan_speed
                globals.WC_DATA_OUT[0]["wc_fan_percent"] = fan_status
                globals.WC_DATA_OUT[0]["wc_pump_speed"] = wc_pump_speed
                globals.WC_DATA_OUT[0]["cpu_degree"] = round(cpu_temp, 1)
                globals.WC_DATA_OUT[0]["cpu_average_degree"] = round(
                    cpu_average_temp, 1)
                globals.WC_DATA_OUT[0]["array_color"] = array_color

                time.sleep(3)
    else:
        raise SystemExit(
            'no devices matches available drivers and selection criteria')
    return None
