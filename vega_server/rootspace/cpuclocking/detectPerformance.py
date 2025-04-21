from utils.processList import get_process_list

app_list = ["vmware", "virtualbox"]


def detect_performance_apps(process_list):
    for app in app_list:
        if app in process_list:
            return True

    return False
