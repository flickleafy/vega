#!/bin/bash

pyinstaller -F -n vega-server-gateway vega_server/gateway/main.py
pyinstaller -F -n vega-server-root vega_server/rootspace/main.py
pyinstaller -F -n vega-server-user vega_server/userspace/main.py
pyinstaller -F -n vega-client vega_client/main.py