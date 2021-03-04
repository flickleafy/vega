# VEGA - Simple dynamic watercooler controller

A simple dynamic watercooler controller. Should work in any Linux.

# Dependencies

It uses [liquidctl](https://github.com/liquidctl/liquidctl) as its basis.
The first version was made in bash, with parts of internal calculations using Python, and parts using bc.
The second version is entirely made in Python.

# Cababilities

1. Dynamic control lighting gradually using math formulas. First assign a degree to a wavelength, convert wavelength to RGB, and then RGB to Hexadecimal RGB.
2. Dynamic control Fan speed gradually based on temperatures using math formulas.
3. Control any watercooler that is supported by liquidctl
4. Smooth transitions, averaging the last 4 temperature values.

# Installation

One possible way to keep it running in background is using cronjob.

On terminal, run:

    sudo crontab -e

In the editor that is opened, you can type this:

## For bash version

> @reboot /path/to/file/watercooler.sh

- **@reboot:** this will start the script as soon Linux is loaded
- **/path/to/file/:** this is where the script is located

## For Python version

> @reboot $(which python3) /path/to/file/watercooler.py >> /path/to/file/watercooler.log 2>&1

- **$(which python3)** this gets the location from Python
- **>>** this will append the output from the script to the watercooler.log
- **2>&1** this gets the standard output and the error output to the same log.
