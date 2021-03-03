# Converting watercooler.sh to Python codes

import ast
import logging
import math
import sys
import time

import liquidctl.cli as liquidAPI
from liquidctl.util import normalize_profile, interpolate_profile, color_from_str
from liquidctl.driver import *

if sys.platform.startswith('linux') or sys.platform.startswith('freebsd'):
    import psutil


def assignDegreeToWavelength(degree):

    minimumDegree = 34.2
    maximumDegree = 45.5
    minimumWavelength = 380
    maximumWavelength = 780
    percentPosition = ((degree - minimumDegree) * 100 /
                       (maximumDegree - minimumDegree))/100
    wavelength = minimumWavelength * (percentPosition + 1)

    return wavelength


def normalizeIntegerColor(IntensityMax, factor, gamma, color):

    color = abs(color)

    color = round(IntensityMax * pow(color * factor, gamma))

    color = min(255, color)
    color = max(0, color)

    return color


def rgbToHexa(red, green, blue):

    red = format(red, 'x')
    green = format(green, 'x')
    blue = format(blue, 'x')

    list = [red, green, blue]

    for x in range(len(list)):
        if len(list[x]) < 2:
            list[x] = "0" + list[x]

    hexString = ""
    for x in list:
        hexString = hexString + x

    return hexString


def wavelengthToRGB(wavelength):
    gamma = 0.80
    IntensityMax = 255
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
        red = normalizeIntegerColor(IntensityMax, factor, gamma, red)

    if (green != 0):
        green = normalizeIntegerColor(IntensityMax, factor, gamma, green)

    if (blue != 0):
        blue = normalizeIntegerColor(IntensityMax, factor, gamma, blue)

    hexaRGB = rgbToHexa(red, green, blue)

    return hexaRGB


def setLedColor(watercoolers, wc_liquid_temp):
    if len(watercoolers) == 1:
        device = watercoolers[0]

        wavelength = assignDegreeToWavelength(wc_liquid_temp)
        color = wavelengthToRGB(wavelength)

        map_color = map(color_from_str, {color})

        device.set_color("led", "fixed", map_color)

    print("RGB color in hexa ", color)
    return True

###


def setFanSpeed(watercoolers, degree):
    if len(watercoolers) == 1:
        device = watercoolers[0]
        speed = 0

        if degree <= 30:
            speed = round(degree + 0.5)

        elif (degree > 30) and (degree <= 40):
            speed = round(degree * (1 + (0.10*(degree - 30))))

        elif (degree > 40) and (degree <= 48):
            speed = round(degree*2.08)

        else:
            speed = 100

        print("Fan speed set to ", speed, "per cent")
        device.set_fixed_speed("fan", speed)

    return True


def status(watercoolers):
    wcstatus = ''
    if len(watercoolers) == 1:
        device = watercoolers[0]
        wcstatus = device.get_status()
    return wcstatus


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
            except:
                time.sleep(3)
                pass

        return watercoolers
    else:
        return 0


def listAverage(list):
    average = sum(list) / len(list)
    return average


def removeFirstAddLast(list, last):
    del list[0]
    list.append(last)
    return list


if __name__ == '__main__':
    wc_last_degrees_list = 0
    watercoolers = initialize()
    if len(watercoolers) > 0:
        while True:

            wc_status = status(watercoolers)
            wc_degree = wc_status[0][1]
            wc_fan_speed = wc_status[1][1]
            wc_pump_speed = wc_status[2][1]

            if wc_last_degrees_list == 0:
                wc_last_degrees_list = [wc_degree,
                                        wc_degree, wc_degree, wc_degree]

            wc_last_degrees_list = removeFirstAddLast(
                wc_last_degrees_list, wc_degree)

            wc_average_degree = listAverage(wc_last_degrees_list)

            setLedColor(watercoolers, wc_average_degree)
            setFanSpeed(watercoolers, wc_average_degree)

            print("Liquid temp ", wc_degree)
            print("Average last temps", wc_average_degree)
            print("Fans speed ", wc_fan_speed)
            print("Pump speed ", wc_pump_speed, "\n")

            time.sleep(3)
    else:
        raise SystemExit(
            'no devices matches available drivers and selection criteria')
