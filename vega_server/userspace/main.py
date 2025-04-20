from threading import Thread, Event

import server.svUserThread as svUserThread
import lighting.lightingThread as ltThread
import watercooler.wcThread as wcThread

import globals

globals.init()

if __name__ == "__main__":

    x = Thread(target=wcThread.watercooler_thread, args=(1,))
    x.start()

    y = Thread(target=svUserThread.server_thread, args=(1,))
    y.start()

    w = Thread(target=ltThread.lighting_thread, args=(1,))
    w.start()
