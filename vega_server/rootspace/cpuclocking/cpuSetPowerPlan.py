# echo powersave | pk tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
# powersave
# schedutil
# performance
from globals import ERROR_MESSAGE
import utils.subProcess as sub_process


def set_powerplan(powerplan):
    try:
        cmd = [
            "echo {0}".format(powerplan),
            "| tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"
        ]
        sub_process.run_cmd(cmd)
    except Exception as err:
        print(ERROR_MESSAGE, err)
