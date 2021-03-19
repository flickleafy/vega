# Converting watercooler.sh to Python codes

import ast
import logging
import math
import sys
import time

import liquidctl.cli as liquidAPI
from liquidctl.util import color_from_str
from liquidctl.driver import *

if sys.platform.startswith('linux') or sys.platform.startswith('freebsd'):
    import psutil


def assign_degree_to_wavelength(degree):

    degree_min = 33.0
    degree_max = 48.0
    degree_range = degree_max - degree_min
    wavel_min = 380
    wavel_max = 780
    wavel_range = wavel_max - wavel_min

    wavelength = (((degree - degree_min) * wavel_range) /
                  degree_range) + wavel_min

    return wavelength


def normalize_integer_color(intensity_max, factor, gamma, color):

    color = abs(color)

    color = round(intensity_max * pow(color * factor, gamma))

    color = min(255, color)
    color = max(0, color)

    return color


def rgb_to_hexa(red, green, blue):

    red = format(red, 'x')
    green = format(green, 'x')
    blue = format(blue, 'x')

    color_list = [red, green, blue]

    for x in range(len(color_list)):
        if len(color_list[x]) < 2:
            color_list[x] = "0" + color_list[x]

    hexa_rgb = ""
    for x in color_list:
        hexa_rgb = hexa_rgb + x

    return hexa_rgb


def wavel_to_rgb(wavelength):
    gamma = 0.80
    intensity_max = 255
    factor = 0.0
    red = 0
    green = 0
    blue = 0

    if (wavelength >= 380) and (wavelength < 440):
        red = (wavelength - 440) / (440 - 380)
        green = 0
        blue = 1.0

    elif (wavelength >= 440) and (wavelength < 490):
        red = 0
        green = (wavelength - 440) / (490 - 440)
        blue = 1.0

    elif (wavelength >= 490) and (wavelength < 510):
        red = 0
        green = 1.0
        blue = (wavelength - 510) / (510 - 490)

    elif (wavelength >= 510) and (wavelength < 580):
        red = (wavelength - 510) / (580 - 510)
        green = 1.0
        blue = 0

    elif (wavelength >= 580) and (wavelength < 645):
        red = 1.0
        green = (wavelength - 645) / (645 - 580)
        blue = 0

    elif (wavelength >= 645) and (wavelength < 781):
        red = 1.0
        green = 0
        blue = 0

    # Reduce intensity near the vision limits

    if (wavelength >= 380) and (wavelength < 420):
        factor = 0.3 + 0.7 * (wavelength - 380)/(420 - 380)

    elif (wavelength >= 420) and (wavelength < 701):
        factor = 1.0

    elif (wavelength >= 701) and (wavelength < 781):
        factor = 0.3 + 0.7 * (780 - wavelength)/(780 - 700)

    if (red != 0):
        red = normalize_integer_color(intensity_max, factor, gamma, red)

    if (green != 0):
        green = normalize_integer_color(intensity_max, factor, gamma, green)

    if (blue != 0):
        blue = normalize_integer_color(intensity_max, factor, gamma, blue)

    hexa_rgb = rgb_to_hexa(red, green, blue)

    return hexa_rgb


def set_led_color(watercoolers, wc_liquid_temp):
    if len(watercoolers) == 1:
        device = watercoolers[0]

        wavelength = assign_degree_to_wavelength(wc_liquid_temp)
        color = wavel_to_rgb(wavelength)

        map_color = map(color_from_str, {color})

        device.set_color("led", "fixed", map_color)

    status = "RGB color set to " + color
    return status

###


def set_fan_speed(watercoolers, degree):
    status = ""
    if len(watercoolers) == 1:
        device = watercoolers[0]
        speed = 0

        if degree <= 30:
            speed = round(degree + 0.5)

        elif (degree > 30) and (degree <= 40):
            speed = round(degree * (1 + (0.10*(degree - 30))))
            speed = min(100, speed)

        elif (degree > 40) and (degree <= 48):
            speed = round(degree*2.08)

        else:
            speed = 100

        status = "Fan speed set to " + str(speed) + " per cent"
        device.set_fixed_speed("fan", speed)

    return status


def status(watercoolers):
    wcstatus = ''
    if len(watercoolers) == 1:
        device = watercoolers[0]
        wcstatus = device.get_status()
    return wcstatus


def cpu_status():
    sensor = ""
    if sys.platform.startswith('linux') or sys.platform.startswith('freebsd'):
        for m, li in psutil.sensors_temperatures().items():
            for label, current, _, _ in li:
                if label.lower().replace(' ', '_') == "tdie":
                    sensor = current

    return sensor


def initialize():
    watercoolers = list(liquidAPI.find_liquidctl_devices())
    if len(watercoolers) > 0:
        device = watercoolers[0]

        result = None
        while result is None:
            try:
                # connect
                result = device.connect()
                device.initialize()
            except Exception as err:
                print("An error have happened: ", err)
                time.sleep(3)

        return watercoolers
    else:
        return 0


def list_average(list):
    average = sum(list) / len(list)
    return average


def remove_first_add_last(list, last):
    del list[0]
    list.append(last)
    return list


if __name__ == '__main__':
    wc_last_degrees = 0
    cpu_last_degrees = 0
    watercoolers = initialize()
    if len(watercoolers) > 0:
        while True:

            wc_status = status(watercoolers)
            wc_degree = wc_status[0][1]
            wc_fan_speed = wc_status[1][1]
            wc_pump_speed = wc_status[2][1]
            cpu_degree = cpu_status()

            if wc_last_degrees == 0:
                wc_last_degrees = [wc_degree,
                                   wc_degree, wc_degree, wc_degree, wc_degree]
                cpu_last_degrees = [cpu_degree, cpu_degree,
                                    cpu_degree, cpu_degree, cpu_degree]

            wc_last_degrees = remove_first_add_last(
                wc_last_degrees, wc_degree)
            cpu_last_degrees = remove_first_add_last(
                cpu_last_degrees, cpu_degree)

            wc_average_degree = list_average(wc_last_degrees)
            cpu_average_degree = list_average(cpu_last_degrees)
            weighed_average_degree = (
                wc_average_degree + (cpu_average_degree*0.85))/2

            ledStatus = set_led_color(watercoolers, wc_average_degree)
            fanStatus = set_fan_speed(watercoolers, weighed_average_degree)

            print("Liquid temp ", wc_degree)
            print("CPU temp", cpu_degree)
            print("Average liquid temps", wc_average_degree)
            print("Average cpu temps", cpu_average_degree)
            print("Weighed Average temps", weighed_average_degree)
            print("Fans speed ", wc_fan_speed)
            print("Pump speed ", wc_pump_speed)
            print(ledStatus)
            print(fanStatus)
            print("\n")

            time.sleep(3)
    else:
        raise SystemExit(
            'no devices matches available drivers and selection criteria')
