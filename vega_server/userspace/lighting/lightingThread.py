import globals

import time

import lighting.lightingStatus as lightingStatus
from openrgb.utils import RGBColor
from openrgb.utils import DeviceType

from lighting.lightingColor import aorus_x470_hue_fix


def lighting_thread(_):
    """_summary_

    Args:
        _ (_type_): _description_

    Returns:
        null: simple thread with no returns
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
    return null


def set_device_color(device, array_color):
    print("###")
    print("### Setting device: " +
          device.name + " color: " + str(array_color))
    print("###")
    time.sleep(.15)
    red = array_color[0]
    green = array_color[1]
    blue = array_color[2]
    if (device.type == DeviceType.MOTHERBOARD):
        if "aorus" in device.name.lower():
            set_aorus_color(device, array_color)
        device.set_color(RGBColor(red, green, blue))
    else:
        device.set_color(RGBColor(red, green, blue))
        time.sleep(.15)
        device.update()


def color_not_changed(array_color):
    if globals.COLOR_SIG_LAST:
        color_signature_current = array_color[0] + \
            array_color[1] + array_color[2]
        if globals.COLOR_SIG_LAST == color_signature_current:
            return False
    globals.COLOR_SIG_LAST = array_color[0] + array_color[1] + array_color[2]
    return True


def set_aorus_color(device, array_color):
    new_array_color = aorus_x470_hue_fix(array_color)
    red2 = new_array_color[0]
    green2 = new_array_color[1]
    blue2 = new_array_color[2]
    device.set_color(RGBColor(red2, green2, blue2))
