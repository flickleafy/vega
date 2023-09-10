from liquidctl.driver import *  # NOSONAR
import liquidctl.cli as liquidAPI

import time

from globals import ERROR_MESSAGE


def get_wc_status(watercoolers):
    """_summary_

    Args:
        watercoolers (_type_): _description_

    Returns:
        _type_: _description_
    """
    wcstatus = ''
    if len(watercoolers) == 1:
        device = watercoolers[0]
        wcstatus = device.get_status()
    return wcstatus


def wc_initialize():
    """_summary_

    Returns:
        _type_: _description_
    """
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
                print(ERROR_MESSAGE, err)
                time.sleep(3)

        return watercoolers
    else:
        return 0
