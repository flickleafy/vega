#!/usr/bin/env python3
"""
Main entry point for the vega server userspace component.

Handles initialization and threading of the various server components.
"""

# Add the project root directory to Python path
import os
import sys

# Get the absolute path of the project root directory (two levels up from this file)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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
