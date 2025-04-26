from liquidctl.util import color_from_str
from vega_common.utils.color_utils import (
    rgb_to_hsv,
    hsv_to_rgb,
    rgb_to_hex as rgb_to_hexa,
    normalize_color_value,
    shift_hue,
    adjust_brightness,
    hex_to_rgb,
)
from vega_common.utils.hardware_rgb_profiles import aorus_x470_hue_fix





def assign_degree_to_wavelength(degree: float, degree_min = 30.0, degree_max = 46.0) -> float:
    """Convert a temperature degree to a light wavelength value.

    Maps temperature range (degree_min to degree_max) to wavelength range (380nm to 780nm).

    Args:
        degree (float): Temperature in degrees Celsius

    Returns:
        float: Corresponding wavelength in nanometers
    """
    degree_range = degree_max - degree_min
    wavel_min = 380
    wavel_max = 780
    wavel_range = wavel_max - wavel_min

    if degree <= degree_min:
        degree = degree_min
    if degree >= degree_max:
        degree = degree_max

    wavelength = (((degree - degree_min) * wavel_range) / degree_range) + wavel_min

    return wavelength


def normalize_integer_color(intensity_max: int, factor: float, gamma: float, color: float) -> int:
    """Normalize a color intensity value with gamma correction.

    Args:
        intensity_max (int): Maximum intensity value
        factor (float): Intensity factor
        gamma (float): Gamma correction value
        color (float): Color value to normalize

    Returns:
        int: Normalized color value
    """
    color = abs(color)
    color = round(intensity_max * pow(color * factor, gamma))
    return normalize_color_value(color, 0, 255)


def wavel_to_rgb(wavelength: float, degree: float, degree_min = 30.0, degree_max = 46.0) -> str:
    """Convert wavelength to RGB color representation.

    Maps light wavelength to corresponding RGB color with intensity
    adjustments based on human color perception.

    Args:
        wavelength (float): Light wavelength in nanometers
        degree (float): Temperature in degrees Celsius

    Returns:
        str: Hexadecimal RGB color string
    """
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
        factor = 0.3 + 0.7 * (wavelength - 380) / (420 - 380)

    elif (wavelength >= 420) and (wavelength < 701):
        factor = 1.0

    elif (wavelength >= 701) and (wavelength < 781):
        factor = 0.3 + 0.7 * (780 - wavelength) / (780 - 700)

    # Further reduce intensity far vision limits
    if degree < degree_min:
        factor = (degree - 5) / 101
    elif degree > degree_max:
        factor = (degree - 15) / 101

    factor = min(1.0, factor)
    factor = max(0.0, factor)

    if red != 0:
        red = normalize_integer_color(intensity_max, factor, gamma, red)

    if green != 0:
        green = normalize_integer_color(intensity_max, factor, gamma, green)

    if blue != 0:
        blue = normalize_integer_color(intensity_max, factor, gamma, blue)

    hexa_rgb = rgb_to_hexa(red, green, blue)

    return hexa_rgb


def set_led_color(devices, index, wc_liquid_temp: float):
    """Set LED colors based on water cooling liquid temperature.

    Args:
        devices (list): List of watercooler devices
        index (int): Index of the device to set color for
        wc_liquid_temp (float): Liquid temperature in degrees Celsius

    Returns:
        list: RGB color values as [r, g, b]
    """
    array_color = [0, 0, 0]
    if len(devices) > 0:
        device = devices[index]

        wavelength = assign_degree_to_wavelength(wc_liquid_temp)
        hexa_rgb = wavel_to_rgb(wavelength, wc_liquid_temp)
        map_color = map(color_from_str, {hexa_rgb})
        array_color = color_from_str(hexa_rgb)

        device.set_color("led", "fixed", map_color)

    return array_color


def increase_light(array_hsv: list, light: int) -> list:
    """Increase the light/value component in an HSV color.

    Args:
        array_hsv (list): HSV values as a list [h, s, v]
        light (int): Amount to increase light by

    Returns:
        list: Updated HSV values
    """
    # Use adjust_brightness from common utilities instead of manual adjustment
    return adjust_brightness(array_hsv.copy(), light)


def normalize_integer(color: int, minimum: int, maximum: int) -> int:
    """Normalize an integer value to be within a specific range.

    Args:
        color (int): Value to normalize
        minimum (int): Minimum allowed value
        maximum (int): Maximum allowed value

    Returns:
        int: Normalized value
    """
    # Use normalize_color_value from common utilities
    return normalize_color_value(color, minimum, maximum)


# The aorus_x470_hue_fix function has been moved to vega_common.utils.hardware_rgb_profiles
# Use the imported function instead
