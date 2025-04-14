# Set GPU fan speed %
# nvidia-settings -a [gpu:0]/GPUFanControlState=1 -a [fan:0]/GPUTargetFanSpeed=20
import gpucooler.gpu_control.gpuDegreeToSpeed as gpuDegreeToSpeed
from globals import ERROR_MESSAGE
import vega_common.utils.sub_process as sub_process
from typing import Optional
import gpucooler.nvidiaex.pynvml as pynvml

FAN_ID = [[0, 1], [2, 3]]


def set_gpu_fan_speed(device_id, degree):
    """_summary_

    Args:
        device_id (_type_): _description_
        degree (_type_): _description_

    Returns:
        _type_: _description_
    """
    speed_fan0 = gpuDegreeToSpeed.degree_to_speed(degree, 0.001)
    speed_fan1 = gpuDegreeToSpeed.degree_to_speed(degree, 0.05)
    set_fan_speed(device_id, speed_fan0, speed_fan1)

    return (speed_fan0, speed_fan1)


def set_fan_speed(device_id: int, speed1: int, speed2: int) -> Optional[str]:
    # Initialize NVML
    try:
        pynvml.nvmlInit()
    except pynvml.NVMLError as error:
        return f"Failed to initialize NVML: {str(error)}"

    try:
        # Get handle to the specific device
        handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)

        num_fans = pynvml.nvmlDeviceGetNumFans(handle)

        # Set the fan speed
        # This assumes that the device is part of the Tesla or Quadro family,
        # and that the fan speed can be set. This may not be the case for all devices!
        # pynvml.nvmlDeviceSetFanSpeed(handle, speed)
        if num_fans == 1:
            pynvml.nvmlDeviceSetFanSpeed_v2(handle, 0, speed1)
        else:
            pynvml.nvmlDeviceSetFanSpeed_v2(handle, 0, speed1)
            pynvml.nvmlDeviceSetFanSpeed_v2(handle, 1, speed2)
        # Cleanup and shutdown NVML
        pynvml.nvmlShutdown()

    except pynvml.NVMLError as error:
        print(f"Failed to set fan speed: {str(error)}")

    return None
