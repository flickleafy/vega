# cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
from globals import ERROR_MESSAGE
import vega_common.utils.sub_process as sub_process


def get_powerplan():
    try:
        cmd = ["cat", "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"]
        result = sub_process.run_cmd(cmd)
        return result
    except Exception as err:
        print(ERROR_MESSAGE, err)
