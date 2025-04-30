from globals import ERROR_MESSAGE
import vega_common.utils.sub_process as sub_process
import gpucooler.gpu_configuration.multiscreens as multiscreens
import gpucooler.gpu_configuration.coolbits as coolbits

from vega_common.utils.logging_utils import get_module_logger

# Setup module-specific logging
logger = get_module_logger("vega_server/rootspace/gpucooler/gpu_configuration")


def configure_gpus():
    """Automatically enable fans creating headless Display configuration"""
    if not multiscreens.layout_has_multi_screens():
        enable_all_gpus()
    if not coolbits.displays_has_coolbits():
        enable_coolbits()
        return None


def enable_all_gpus():
    try:
        cmd = ["nvidia-xconfig", "--enable-all-gpus"]
        result = sub_process.run_cmd(cmd)
        return result
    except Exception as err:
        logger.error(f"{ERROR_MESSAGE} {err}")


def enable_coolbits():
    try:
        cmd = ["nvidia-xconfig", "--cool-bits=29"]
        result = sub_process.run_cmd(cmd)
        return result
    except Exception as err:
        logger.error(f"{ERROR_MESSAGE} {err}")
