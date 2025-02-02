import globals

import time
import utils.listProcess as listProcess
import watercooler.wcStatus as wcStatus
import watercooler.cpuStatus as cpuStatus
import lighting.lightingColor as lightingColor
import watercooler.wcTemp as wcTemp

VALUE_COLUMN = 1
LIQUID_TEMPERATURE_ROW = 0
FAN_SPEED_ROW = 1
PUMP_SPEED_ROW = 2
                
def watercooler_thread(_):
    """_summary_

    Args:
        _ (_type_): _description_

    Raises:
        SystemExit: _description_

    Returns:
        null: simple thread with no returns
    """
    wc_last_temps = 0
    cpu_last_temps = 0
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
                    cpu_temp = estimate_from_wc_temp(wc_temp)

                if wc_last_temps == 0:
                    wc_last_temps = [wc_temp] * 7

                    cpu_last_temps = [cpu_temp] * 7

                wc_last_temps = listProcess.remove_first_add_last(
                    wc_last_temps, wc_temp)
                cpu_last_temps = listProcess.remove_first_add_last(
                    cpu_last_temps, cpu_temp)

                wc_average_temp = listProcess.list_average(wc_last_temps)
                cpu_average_temp = listProcess.list_average(cpu_last_temps)
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
    return null


def estimate_from_wc_temp(wc_temp):
    cpu_temp = (-727.5 + (30 * wc_temp)) / 7.5
    return cpu_temp
