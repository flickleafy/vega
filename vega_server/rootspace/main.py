from threading import Thread, Event

import server.svRootThread as svRootThread
import cpuclocking.cpuClockingThread as ccThread

import globals
import gpucooler.gpuThread as gtThread

globals.init()

if __name__ == "__main__":

    v = Thread(target=ccThread.cpuclocking_thread, args=(1,))
    v.start()

    z = Thread(target=gtThread.gpu_thread, args=(1,))
    z.start()
    # z.join()

    y = Thread(target=svRootThread.server_thread, args=(1,))
    y.start()
    # y.join()
