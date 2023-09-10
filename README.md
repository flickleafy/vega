# VEGA - Dynamic cooling, lighting and clocking controller

A dynamic cooling (watercooler, cpu, and gpu) controller, dynamic lighting controller (any device supported by openRGB), and dynamic cpu clocking controller. Should work in any Linux that supports the project dependencies.

# Dependencies

It uses [liquidctl](https://github.com/liquidctl/liquidctl) as its basis for the watercooler controlling.\
It uses [openRGB](https://gitlab.com/CalcProgrammer1/OpenRGB) for ligthing controlling for RAM, Motherboard, and couple other devices supported by openRGB.\
It uses [nvidia-settings]()/[nvidia-smi]() to controll gpu temperature and fans, and in the future, it is planned to controll other GPU parameters.

# Capabilities

1. Dynamic control lighting gradually using math formula (first assign a degree to a wavelength, convert wavelength to RGB, and then RGB to Hexadecimal RGB).
2. Dynamic control Fan speed gradually based on temperatures using math formula.
3. Control any watercooler that is supported by liquidctl.
4. Smooth transitions, averaging the last recorded temperature values.
5. Control GPU individual fans (for Nvidia compatible GPUs), monitoring temperature and calculating an optimal speed.
6. Control CPU clocking by changing the power plan based in key applications that may be running.
7. Control CPU clocking by changing the power plan based in limit of CPU temperatures.

# Installation

## Server-side configuration

### Cronjob configuration (as root) for vega-server-root

On terminal, run:

> sudo crontab -e

In the editor that is opened, you can type this:

> @reboot /path/to/file/vega-server-root >> /path/to/file/vega-server-root.log 2>&1

- **@reboot:** this will start the script as soon Linux is loaded
- **/path/to/file/:** this is where the script is located
- **>>** this will append the output from the script to the vega-server-root.log
- **2>&1** this gets the standard output and the error output to the same log.

### Startup configuration for vega-server-user

> sh -c "/path/to/file/vega-server-user >> /path/to/file/vega-server-user.log 2>&1"

### Startup configuration for vega-server-gateway

> sh -c "/path/to/file/vega-server-gateway >> /path/to/file/vega-server-gateway.log 2>&1"


## Client-side configuration

Startup configuration for client-side app.

> sh -c "/path/to/file/vega-server-user >> /path/to/file/vega-server-user.log 2>&1"

# Package building

From root of the project:

## For Python Vega-server

> pyinstaller -F -n vega-server-gateway vega_server/gateway/main.py

> pyinstaller -F -n vega-server-root vega_server/rootspace/main.py

> pyinstaller -F -n vega-server-user vega_server/userspace/main.py

## For Python Vega-client

> pyinstaller -F -n vega-client vega_client/main.py
