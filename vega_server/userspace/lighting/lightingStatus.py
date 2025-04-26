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
    print("###")
    print("### Getting OpenRGB devices")
    print("###")
    time.sleep(0.15)
    open_rgb.update()
    time.sleep(0.15)
    rams = open_rgb.get_devices_by_type(DeviceType.DRAM)
    motherboard = open_rgb.get_devices_by_type(DeviceType.MOTHERBOARD)
    gpus = open_rgb.get_devices_by_type(DeviceType.GPU)
    devices = rams + motherboard + gpus

    for device in devices:
        try:
            print("### Reseting device " + device.name)
            print("###")
            time.sleep(0.15)
            device.clear()
            time.sleep(0.15)
            if "corsair dominator platinum" in device.name.lower():
                device.set_mode("direct")
            elif device.type == DeviceType.GPU:
                # GPUs need special handling: switch to a different mode first,
                # then back to static to ensure color changes work properly
                device.set_mode("direct")
                time.sleep(0.15)
                device.set_mode("static")
            else:
                device.set_mode("off")
                time.sleep(0.15)
                device.set_mode("static")
        except Exception as e:
            print(f"### Error initializing device {device.name}: {e}")
            print("### Continuing with next device...")
            continue

    return devices  # cooler, gpu, handle
