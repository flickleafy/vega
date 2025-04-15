import globals

import time

import lighting.lightingStatus as lightingStatus
from openrgb.utils import RGBColor
from openrgb.utils import DeviceType

from lighting.lightingColor import aorus_x470_hue_fix
from vega_common.utils.color_utils import calculate_color_signature


def lighting_thread(_):
    """Monitor and control device lighting based on temperature data.

    This thread continuously updates connected RGB devices with colors
    based on temperature data. Supports various RGB device types with
    special handling for specific devices like AORUS motherboards.

    Args:
        _ (int): Unused argument, maintained for thread function signature consistency.

    Returns:
        None: This thread runs continuously.
    """

    devices = lightingStatus.init_lighting()
    while True:
        try:
            for device in devices:
                try:
                    array_color = globals.WC_DATA_OUT[0]["array_color"]
                except Exception as err:
                    print('### Error reading global structure', err)
                    continue
                if isinstance(array_color, list):
                    set_device_color(device, array_color)

            time.sleep(3)
        except (ConnectionResetError, BrokenPipeError, TimeoutError) as e:
            print(str(e) + " during main loop")
            print("Trying to reconnect...")
            lightingStatus.init_lighting()
    return None


def rgb_to_rgbcolor(rgb_array: list) -> RGBColor:
    """Convert a standard RGB array to an OpenRGB RGBColor object.
    
    Args:
        rgb_array (list): RGB values as [r, g, b]
        
    Returns:
        RGBColor: OpenRGB color object
    """
    if not rgb_array or len(rgb_array) < 3:
        return RGBColor(0, 0, 0)
        
    r = rgb_array[0]
    g = rgb_array[1]
    b = rgb_array[2]
    return RGBColor(r, g, b)


def set_device_color(device, array_color):
    """Set the color for an RGB device with appropriate handling for device types.
    
    Args:
        device: The OpenRGB device object to control
        array_color (list): RGB values as [r, g, b]
    """
    print("###")
    print("### Setting device: " +
          device.name + " color: " + str(array_color))
    print("###")
    
    # Use small delay to avoid overwhelming the device controller
    time.sleep(.15)
    
    # Special handling for AORUS motherboards which need color correction
    if (device.type == DeviceType.MOTHERBOARD and "aorus" in device.name.lower()):
        corrected_color = aorus_x470_hue_fix(array_color)
        rgb_color = rgb_to_rgbcolor(corrected_color)
    else:
        rgb_color = rgb_to_rgbcolor(array_color)
    
    # Set the color on the device
    device.set_color(rgb_color)
    
    # Some devices need an explicit update call
    if device.type != DeviceType.MOTHERBOARD:
        time.sleep(.15)
        device.update()


def color_not_changed(array_color):
    """Check if the color has changed from the last update.
    
    Uses a color signature approach to detect changes in RGB values.
    
    Args:
        array_color (list): RGB color as [r, g, b]
        
    Returns:
        bool: True if color has changed, False otherwise
    """
    # Calculate the color signature using common utility
    color_signature_current = calculate_color_signature(array_color)
    
    if globals.COLOR_SIG_LAST and globals.COLOR_SIG_LAST == color_signature_current:
        return False
        
    globals.COLOR_SIG_LAST = color_signature_current
    return True


def set_aorus_color(device, array_color):
    """Set color for AORUS motherboards with special color correction.
    
    This is a legacy function maintained for backward compatibility.
    New code should use set_device_color instead.
    
    Args:
        device: The OpenRGB device object to control
        array_color (list): RGB values as [r, g, b]
    """
    new_array_color = aorus_x470_hue_fix(array_color)
    rgb_color = rgb_to_rgbcolor(new_array_color)
    device.set_color(rgb_color)
