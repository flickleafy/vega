import globals
import copy

import utils.listProcess as listProcess
import time
import gpucooler.gpu_control.gpuTemp as gpuTemp
import gpucooler.gpu_control.gpuStatus as gpuStatus
import gpucooler.gpu_configuration.gpuDisplay as gpuDisplay


def gpu_thread(_):
    """_summary_

    Args:
        _ (_type_): _description_

    Returns:
        null: simple thread with no returns
    """
    gpus_last_degrees = [0, 0]

    gpuDisplay.configure_gpus()
    gpus = gpuStatus.get_device_count()
    while True:
        gpus_status = gpuStatus.get_gpu_status()

        for i in range(0, gpus):
            gpu_status = gpus_status[i]

            if gpus_last_degrees[i] == 0:
                gpus_last_degrees[i] = [gpu_status["temp"]] * 10

            gpus_last_degrees[i] = listProcess.remove_first_add_last(
                gpus_last_degrees[i], gpu_status["temp"])

            gpu_average_degree = listProcess.list_average(gpus_last_degrees[i])

            fan_set_speed = gpuTemp.set_gpu_fan_speed(i, gpu_average_degree)
            gpu_status["s_speed1"] = fan_set_speed[0]
            gpu_status["s_speed2"] = fan_set_speed[1]

            print('######################')
            print('#')
            print('GPU id', gpu_status["id"])
            print('device name', gpu_status["name"])
            print('GPU current fan1 speed', gpu_status["c_speed1"])
            print('GPU current fan2 speed', gpu_status["c_speed2"])
            print('GPU set fan1 speed', gpu_status["s_speed1"])
            print('GPU set fan2 speed', gpu_status["s_speed2"])
            print('GPU temp', gpu_status["temp"])
            print("GPU Average temps", gpu_average_degree)
            print('#')
            print('######################')

            globals.WC_DATA_OUT[0]["gpu" +
                                   str(i) + "_degree"] = round(gpu_status["temp"], 1)
            globals.WC_DATA_OUT[0]["gpu" +
                                   str(i) + "_average_degree"] = round(
                gpu_average_degree, 1)
            globals.WC_DATA_OUT[0]["gpu" +
                                   str(i) + "_c_fan_speed1"] = gpu_status["c_speed1"]
            globals.WC_DATA_OUT[0]["gpu" +
                                   str(i) + "_c_fan_speed2"] = gpu_status["c_speed2"]
            globals.WC_DATA_OUT[0]["gpu" +
                                   str(i) + "_s_fan_speed1"] = gpu_status["s_speed1"]
            globals.WC_DATA_OUT[0]["gpu" +
                                   str(i) + "_s_fan_speed2"] = gpu_status["s_speed2"]
            # NOSONAR
            # globals.WC_DATA_OUT[0]["gpu_fan_percent"] = fan_status

        time.sleep(3)

    return null
