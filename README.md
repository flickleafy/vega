# VEGA - Simple dynamic watercooler controller

A simple dynamic watercooler controller made in bash script. Should work in any Linux.

# Dependencies

It uses [liquidctl](https://github.com/liquidctl/liquidctl) as its basis, and parts of internal calculations is using Python [I know, I should have done it entirely in Python :-) but, when I started, it was made to be as simple as possible]

# Cababilities

1. Dynamic control lighting gradually using math formulas. First assign a degree to a wavelength, convert wavelength to RGB, and then RGB to Hexadecimal RGB.
2. Dynamic control Fan speed gradually based on temperatures using math formulas.
3. Control any watercooler that is supported by liquidctl

# Installation

One possible way to keep it running in background is as a cronjob.

On terminal, run:

    sudo crontab -e

In the editor that is opened, you can type this:

> @reboot /path/to/file/watercooler.sh

- **@reboot:** this will start the script as soon Linux is loaded
- **/path/to/file/:** this is where the script is located
