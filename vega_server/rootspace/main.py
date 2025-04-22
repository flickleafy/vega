#!/usr/bin/env python3
"""
Main entry point for the vega server rootspace component.

Handles initialization and threading of the various server components.
"""

# Add the project root directory to Python path
import os
import sys

# Get the absolute path of the project root directory (two levels up from this file)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added project root to Python path: {project_root}")

from threading import Thread, Event

import server.svRootThread as svRootThread
import cpuclocking.cpuClockingThread as ccThread

import globals
import gpucooler.gpuThread as gtThread

globals.init()

if __name__ == "__main__":
    # Create and start CPU clocking thread
    v = Thread(target=ccThread.cpuclocking_thread, args=(1,))
    v.start()

    # Create and start GPU cooling thread
    z = Thread(target=gtThread.gpu_thread, args=(1,))
    z.start()
    # z.join()  # Uncomment to wait for GPU thread to finish

    # Create and start server thread
    y = Thread(target=svRootThread.server_thread, args=(1,))
    y.start()
    # y.join()  # Uncomment to wait for server thread to finish
