
from threading import Thread, Event

import server.svGWThread as svGWThread
import client.ctRootThread as ctRootThread
import client.ctUserThread as ctUserThread

import globals
globals.init()

if __name__ == '__main__':

    z = Thread(target=ctRootThread.client_thread, args=(1,))
    z.start()

    z = Thread(target=ctUserThread.client_thread, args=(1,))
    z.start()

    y = Thread(target=svGWThread.server_thread, args=(1,))
    y.start()
