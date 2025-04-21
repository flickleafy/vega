from liquidctl.driver import *  # NOSONAR
import liquidctl.cli as liquidAPI

import time

from globals import ERROR_MESSAGE


def get_wc_status(devices, index):
    """_summary_

    Args:
        watercoolers (_type_): _description_

    Returns:
        _type_: _description_
    """
    device_status = ""

    device = devices[index]
    device_status = device.get_status()

    return device_status


def wc_initialize():
    """_summary_

    Returns:
        _type_: _description_
    """
    devices = list(liquidAPI.find_liquidctl_devices())
    if len(devices) > 0:
        for index, device in enumerate(devices):
            result = None
            while result is None:
                try:
                    # connect
                    result = device.connect()
                    device.initialize()
                except Exception as err:
                    print(ERROR_MESSAGE, err)
                    time.sleep(3)

        return devices
    else:
        return 0
