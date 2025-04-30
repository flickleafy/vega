import os
import sys
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
gi.require_version("Notify", "0.7")

from gi.repository import Gtk as gtk
from gi.repository import GLib as glib
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify

import globals
from vega_common.utils.logging_utils import get_module_logger

# Setup module-specific logging
logger = get_module_logger("vega_client/taskbar")

APPINDICATOR_ID = "vega_client"


def get_icon_path():
    """
    Get the path to the icon file, handling both development and bundled executable scenarios.
    
    When running as a PyInstaller bundle, sys._MEIPASS points to the temp extraction directory.
    Otherwise, look for the icon relative to this script's location.
    """
    icon_name = "cpu_v.png"
    
    # Check if running as a PyInstaller bundle
    if hasattr(sys, '_MEIPASS'):
        # Running as bundled executable - icon is in the extraction directory
        return os.path.join(sys._MEIPASS, icon_name)
    else:
        # Running in development - icon is in the same directory as this script
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), icon_name)


def app_indicator():
    icon_dir = get_icon_path()
    indicator = appindicator.Indicator.new(
        APPINDICATOR_ID, icon_dir, appindicator.IndicatorCategory.SYSTEM_SERVICES
    )

    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)

    indicator.set_menu(build_menu(indicator))

    notify.init(APPINDICATOR_ID)
    glib.timeout_add(1000, change_label, indicator)

    gtk.main()


def get_checked_variable(var_type: str, variable, key: str):
    degree = "°C"
    string = ""
    try:
        string = var_type + str(round(variable[key], 1)) + degree
    except Exception as err:
        logger.debug(f"Could not read variable {key}: {err}")

    return string


def change_label(indicator):
    liquid = get_checked_variable("wc_", globals.WC_DATA[0], "wc_degree")
    cpu = get_checked_variable("c_", globals.WC_DATA[0], "cpu_degree")
    gpu0 = get_checked_variable("g0_", globals.WC_DATA[0], "gpu0_degree")
    gpu1 = get_checked_variable("g1_", globals.WC_DATA[0], "gpu1_degree")
    data = cpu + " " + liquid + " " + gpu0 + " " + gpu1

    indicator.set_label(data, "")
    return True


def build_menu(indicator):
    menu = gtk.Menu()

    item_wctemp = gtk.MenuItem("Watercooler Temp")
    item_wctemp.connect("activate", wc_temp)
    menu.append(item_wctemp)

    item_quit = gtk.MenuItem("Quit")
    item_quit.connect("activate", quit)
    menu.append(item_quit)

    menu.show_all()
    return menu


def wc_temp(_):
    try:
        data = str(globals.WC_DATA[0]["wc_degree"]) + "°C"
    except Exception as err:
        data = ""
    notify.Notification.new("Water temperature", data, None).show()


def quit(_):
    notify.uninit()
    gtk.main_quit()
