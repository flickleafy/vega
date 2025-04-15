from liquidctl.util import color_from_str
from vega_common.utils.color_utils import rgb_to_hsv, hsv_to_rgb, rgb_to_hex as rgb_to_hexa, normalize_color_value

degree_min = 30.0
degree_max = 46.0


def assign_degree_to_wavelength(degree: float) -> float:
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

    if (degree <= degree_min):
        degree = degree_min
    if (degree >= degree_max):
        degree = degree_max

    wavelength = (((degree - degree_min) * wavel_range) /
                  degree_range) + wavel_min

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


def wavel_to_rgb(wavelength: float, degree: float) -> str:
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
    if (degree < degree_min):
        factor = (degree - 5) / 101
    elif (degree > degree_max):
        factor = (degree - 15) / 101

    factor = min(1.0, factor)
    factor = max(0.0, factor)

    if (red != 0):
        red = normalize_integer_color(intensity_max, factor, gamma, red)

    if (green != 0):
        green = normalize_integer_color(intensity_max, factor, gamma, green)

    if (blue != 0):
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
    # position 2 is light
    new_light = array_hsv[2] + light
    array_hsv[2] = normalize_integer(new_light, 0, 100)
    return array_hsv


def normalize_integer(color: int, minimum: int, maximum: int) -> int:
    """Normalize an integer value to be within a specific range.
    
    Args:
        color (int): Value to normalize
        minimum (int): Minimum allowed value
        maximum (int): Maximum allowed value
        
    Returns:
        int: Normalized value
    """
    color = abs(color)
    color = round(color)
    color = min(maximum, color)
    color = max(minimum, color)
    return color


def aorus_x470_hue_fix(array_rgb: list) -> list:
    """Apply specific color corrections for the AORUS X470 motherboard.
    
    The AORUS X470 motherboard has issues with certain colors, particularly
    in the blue spectrum. This function provides corrected RGB values based on
    the hue to achieve more accurate display colors.
    
    Args:
        array_rgb (list): RGB values as [r, g, b]
        
    Returns:
        list: Corrected RGB values for the AORUS X470 motherboard
    """
    # Correct AORUS motherboard blue led defect
    array_hsv = rgb_to_hsv(array_rgb)
    if (array_hsv[0] > 295) and (array_hsv[0] <= 360):
        return [7, 1, 255]
    elif (array_hsv[0] > 290) and (array_hsv[0] <= 295):
        return [5, 1, 255]
    elif (array_hsv[0] > 280) and (array_hsv[0] <= 290):
        return [4, 0, 255]
    elif (array_hsv[0] > 270) and (array_hsv[0] <= 280):
        return [3, 1, 255]
    elif (array_hsv[0] > 260) and (array_hsv[0] <= 270):
        return [3, 0, 255]
    elif (array_hsv[0] > 250) and (array_hsv[0] <= 260):
        return [2, 0, 255]
    elif (array_hsv[0] > 240) and (array_hsv[0] <= 250):
        return [1, 1, 255]
    elif (array_hsv[0] > 230) and (array_hsv[0] <= 240):
        return [0, 1, 255]
    elif (array_hsv[0] > 220) and (array_hsv[0] <= 230):
        return [0, 2, 255]
    elif (array_hsv[0] > 210) and (array_hsv[0] <= 220):
        return [0, 4, 255]
    elif (array_hsv[0] > 200) and (array_hsv[0] <= 210):
        return [0, 8, 255]
    elif (array_hsv[0] > 190) and (array_hsv[0] <= 200):
        return [0, 16, 255]
    elif (array_hsv[0] > 180) and (array_hsv[0] <= 190):
        return [0, 28, 255]
    elif (array_hsv[0] > 170) and (array_hsv[0] <= 180):
        return [0, 36, 255]
    elif (array_hsv[0] > 160) and (array_hsv[0] <= 170):
        return [0, 40, 255]
    elif (array_hsv[0] > 150) and (array_hsv[0] <= 160):
        return [0, 44, 255]
    elif (array_hsv[0] > 140) and (array_hsv[0] <= 150):
        return [0, 48, 255]
    elif (array_hsv[0] > 130) and (array_hsv[0] <= 140):
        return [0, 52, 255]
    elif (array_hsv[0] > 120) and (array_hsv[0] <= 130):
        return [0, 80, 255]
    elif (array_hsv[0] > 110) and (array_hsv[0] <= 120):
        return [10, 200, 255]
    elif (array_hsv[0] > 100) and (array_hsv[0] <= 110):
        return [28, 255, 255]
    elif (array_hsv[0] > 90) and (array_hsv[0] <= 100):
        return [38, 255, 255]
    elif (array_hsv[0] > 80) and (array_hsv[0] <= 90):
        return [48, 255, 255]
    elif (array_hsv[0] > 70) and (array_hsv[0] <= 80):
        return [68, 255, 255]
    elif (array_hsv[0] > 60) and (array_hsv[0] <= 70):
        return [40, 120, 255]
    elif (array_hsv[0] > 50) and (array_hsv[0] <= 60):
        return [40, 110, 255]
    elif (array_hsv[0] > 40) and (array_hsv[0] <= 50):
        return [50, 110, 255]
    elif (array_hsv[0] > 30) and (array_hsv[0] <= 40):
        return [65, 110, 255]
    elif (array_hsv[0] > 20) and (array_hsv[0] <= 30):
        return [100, 90, 255]
    elif (array_hsv[0] > 10) and (array_hsv[0] <= 20):
        return [110, 70, 255]
    elif (array_hsv[0] > 5) and (array_hsv[0] <= 10):
        return [140, 50, 255]
    elif (array_hsv[0] >= 0) and (array_hsv[0] <= 5):
        return [255, 20, 255]
