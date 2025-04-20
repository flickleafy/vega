import globals
import time
from cpuclocking.cpuGetPowerPlan import get_powerplan
from cpuclocking.cpuSetPowerPlan import set_powerplan
from cpuclocking.cpuPowerPlanSwitcher import powerplan_switcher


def cpuclocking_thread(_):
    """_summary_

    Args:
        _ (_type_): _description_

    Returns:
        null: simple thread with no returns
    """

    time.sleep(60)

    while True:
        try:
            powerplan = powerplan_switcher()
            set_powerplan(powerplan["plan"])
            time.sleep(powerplan["sleep"])
        except Exception as err:
            print(str(err) + " during clocking loop")
    return null
