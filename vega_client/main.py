from threading import Thread, Event
import signal
import time

import client.ctThread as ctThread
import taskbar.appIndicator as aiTaskbar

import globals

globals.init()

if __name__ == "__main__":
    time.sleep(20)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    x = Thread(target=ctThread.client_thread, args=(1,), daemon=True)
    x.start()

    aiTaskbar.app_indicator()
