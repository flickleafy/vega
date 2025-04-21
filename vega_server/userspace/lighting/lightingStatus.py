import time
from openrgb import OpenRGBClient
from openrgb.utils import DeviceType


def init_lighting():
    # Getting this script ready to be run as a service. Waiting for the sdk to start.
    while True:
        try:
            time.sleep(10)
            print("###")
            print("### Connecting to OpenRGB")
            print("###")
            open_rgb = OpenRGBClient()
            break
        except ConnectionRefusedError:
            time.sleep(3)
            continue
    # try:
    # cooler = cli.get_devices_by_type(DeviceType.COOLER)[0]
    # except IndexError:
    # cooler = False
    # try:
    # gpu = cli.get_devices_by_type(DeviceType.GPU)[0]
    # except IndexError:
    # gpu = False
    print("###")
    print("### Getting OpenRGB devices")
    print("###")
    time.sleep(0.15)
    open_rgb.update()
    time.sleep(0.15)
    rams = open_rgb.get_devices_by_type(DeviceType.DRAM)
    motherboard = open_rgb.get_devices_by_type(DeviceType.MOTHERBOARD)
    devices = rams + motherboard

    for device in devices:
        print("### Reseting device " + device.name)
        print("###")
        time.sleep(0.15)
        device.clear()
        time.sleep(0.15)
        if "corsair dominator platinum" in device.name.lower():
            device.set_mode("direct")
        else:
            device.set_mode("off")
            time.sleep(0.15)
            device.set_mode("static")

    # To make sure the devices are in the right mode, and to work around a problem
    #   where the gpu won't change colors until switched out of static mode and
    #   then back into static mode.

    # NOSONAR
    # if gpu:
    #     gpu.set_mode(1)  # Anything would work, this is breathing in my setup
    #     sleep(.1)
    #     gpu.set_mode(0)  # Static mode.  My GPU doesn't have a direct mode.
    #     try:
    #         nvmlInit()
    #         handle = nvmlDeviceGetHandleByIndex(0)
    #     except Exception as err:
    #         gpu, handle = False, False
    # else:
    #     handle = False
    return devices  # cooler, gpu, handle
