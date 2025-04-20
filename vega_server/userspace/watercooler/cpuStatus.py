import sys

if sys.platform.startswith("linux") or sys.platform.startswith("freebsd"):
    import psutil


def get_cpu_status():
    """_summary_

    Returns:
        _type_: _description_
    """
    sensor = 0
    if sys.platform.startswith("linux") or sys.platform.startswith("freebsd"):
        # print(str(psutil.sensors_temperatures()))
        for device, li in psutil.sensors_temperatures().items():
            if device == "nvme":
                dummy = ""
            elif device == "k10temp":
                for label, current, _, _ in li:
                    label = label.lower().replace(" ", "_")
                    if label in ("tdie", "tctl", "tccd1", "tccd2"):
                        sensor = current
                        break
    return sensor
