from cpuclocking.detectBalance import detect_balance_apps
from cpuclocking.detectPerformance import detect_performance_apps
import globals
from vega_common.utils.process_utils import get_process_list


def powerplan_switcher():
    process_list = get_process_list()

    average_degree = 0
    control = ''

    try:
        average_degree = globals.WC_DATA_IN[0]["wc_average_degree"]
    except Exception as err:
        print('Error during access WC_DATA_IN[0]["wc_average_degree"] ', err)

    if average_degree > 39:
        control = 'warm'
    elif average_degree > 42:
        control = 'hot'
    elif detect_performance_apps(process_list):
        control = 'performance'
    elif detect_balance_apps(process_list):
        control = 'balanced'

    match control:
        case 'performance':
            powerplan = {'plan': 'performance', 'sleep': 60}
        case 'balanced':
            powerplan = {'plan': 'schedutil', 'sleep': 120}
        case 'warm':
            powerplan = {'plan': 'powersave', 'sleep': 300}
        case 'hot':
            powerplan = {'plan': 'powersave', 'sleep': 600}
        case _:
            powerplan = {'plan': 'powersave', 'sleep': 10}
    return powerplan
