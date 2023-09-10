from utils.processList import get_process_list

app_list = ['vdf.gui', 'dupeguru', 'celluloid', 'mpv']


def detect_balance_apps(process_list):
    for app in app_list:
        if app in process_list:
            return True

    return False
