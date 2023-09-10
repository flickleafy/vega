import time
import gpucooler.nvidiaex.pynvml as pynvml

# Get GPU list
# nvidia-settings -q gpus

# Get GPU list
# nvidia-smi -L

# Get GPU temperature
# nvidia-settings -q [gpu:0]/GPUCoreTemp | grep xxx-master

# Get GPU temperature
# nvidia-smi -i 0 --query-gpu=temperature.gpu --format=csv,noheader


def get_device_count():
    """_summary_

    Returns:
        _type_: _description_
    """
    while True:
        device_count = 0
        try:
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            print('GPU device count: ' + str(device_count))
        except pynvml.NVMLError as err:
            print('nvidia_smi.py: ' + err.__str__() + '\n')

        if device_count > 0:
            pynvml.nvmlShutdown()
            return device_count

        time.sleep(3)


def get_gpu_status():
    """_summary_

    Returns:
        _type_: _description_
    """
    gpus_status = []
    try:
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        for i in range(0, device_count):
            gpu_info = {
                "id": "",
                "name": "",
                "c_speed1": "",
                "c_speed2": "",
                "s_speed1": "",
                "s_speed2": "",
                "temp": ""
            }
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)

            pci_info = pynvml.nvmlDeviceGetPciInfo(handle)

            num_fans = pynvml.nvmlDeviceGetNumFans(handle)

            fan1 = None
            fan2 = None
            try:
                if num_fans == 1:
                    fan1 = pynvml.nvmlDeviceGetFanSpeed_v2(handle, 0)
                else:
                    fan1 = pynvml.nvmlDeviceGetFanSpeed_v2(handle, 0)
                    fan2 = pynvml.nvmlDeviceGetFanSpeed_v2(handle, 1)
            except pynvml.NVMLError as err:
                if num_fans == 1:
                    fan1 = pynvml.handleError(err)
                else:
                    fan1 = pynvml.handleError(err)
                    fan2 = pynvml.handleError(err)

            try:
                temp = pynvml.nvmlDeviceGetTemperature(
                    handle, pynvml.NVML_TEMPERATURE_GPU)
            except pynvml.NVMLError as err:
                temp = pynvml.handleError(err)

            gpu_info["id"] = pci_info.busId
            gpu_info["name"] = str(pynvml.nvmlDeviceGetName(handle))
            gpu_info["c_speed1"] = fan1
            gpu_info["c_speed2"] = fan2
            gpu_info["temp"] = temp

            gpus_status.append(gpu_info)

    except pynvml.NVMLError as err:
        print('nvidia_smi.py: ' + err.__str__() + '\n')

    pynvml.nvmlShutdown()

    return gpus_status
