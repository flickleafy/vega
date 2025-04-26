import globals

import time

import lighting.lightingStatus as lightingStatus
from openrgb.utils import RGBColor
from openrgb.utils import DeviceType
from openrgb.utils import OpenRGBDisconnected

from vega_common.utils.hardware_rgb_profiles import aorus_x470_hue_fix
from vega_common.utils.color_utils import calculate_color_signature
from vega_common.utils.color_utils import rgb_to_rgbcolor


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
                    print("### Error reading global structure", err)
                    continue
                if isinstance(array_color, list):
                    set_device_color(device, array_color)

            time.sleep(3)
        except (ConnectionResetError, BrokenPipeError, TimeoutError, OpenRGBDisconnected) as e:
            print(str(e) + " during main loop")
            print("Trying to reconnect...")
            devices = lightingStatus.init_lighting()
    return None


def set_device_color(device, array_color):
    """Set the color for an RGB device with appropriate handling for device types.

    Args:
        device: The OpenRGB device object to control
        array_color (list): RGB values as [r, g, b]
    """
    # Check if the color has actually changed since the last update
    # If not, return early to avoid unnecessary device updates
    if not color_not_changed(device, array_color):
        return

    print("###")
    print("### Setting device: " + device.name + " color: " + str(array_color))
    print("###")

    # Use small delay to avoid overwhelming the device controller
    time.sleep(0.15)

    # Special handling for AORUS motherboards which need color correction
    if device.type == DeviceType.MOTHERBOARD and "aorus" in device.name.lower():
        corrected_color = aorus_x470_hue_fix(array_color)
        rgb_color = rgb_to_rgbcolor(corrected_color)
    else:
        rgb_color = rgb_to_rgbcolor(array_color)

    # Set the color on the device
    device.set_color(rgb_color)

    # Some devices need an explicit update call
    if device.type != DeviceType.MOTHERBOARD:
        time.sleep(0.15)
        device.update()


def color_not_changed(device, array_color):
    """Check if the color has changed from the last update for a specific device.

    Uses a color signature approach to detect changes in RGB values.

    Args:
        device: The OpenRGB device object
        array_color (list): RGB color as [r, g, b]

    Returns:
        bool: True if color has changed, False otherwise
    """
    # Calculate the color signature using common utility
    color_signature_current = calculate_color_signature(array_color)
    
    # Use device id() (memory address) as unique key to track color signature per device instance
    # This ensures each physical device gets its own tracking, even if names are identical
    device_key = id(device)
    
    if device_key in globals.COLOR_SIG_LAST and globals.COLOR_SIG_LAST[device_key] == color_signature_current:
        return False

    globals.COLOR_SIG_LAST[device_key] = color_signature_current
    return True
