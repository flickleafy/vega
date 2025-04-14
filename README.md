# VEGA - Dynamic cooling, lighting and clocking controller

A dynamic cooling (watercooler, cpu, and gpu) controller, dynamic lighting controller (any device supported by openRGB), and dynamic cpu clocking controller. Should work in any Linux that supports the project dependencies.

## Dependencies

It uses [liquidctl](https://github.com/liquidctl/liquidctl) as its basis for the watercooler controlling.\
It uses [openRGB](https://gitlab.com/CalcProgrammer1/OpenRGB) for ligthing controlling for RAM, Motherboard, and couple other devices supported by openRGB.\
It uses [nvidia-settings](_)/[nvidia-ml-py](https://pypi.org/project/nvidia-ml-py/) to controll gpu temperature and fans, and in the future, it is planned to controll other GPU parameters.

## Features

1. Dynamic control lighting gradually using math formula (first assign a degree to a wavelength, convert wavelength to RGB, and then RGB to Hexadecimal RGB).
2. Dynamic control Fan speed gradually based on temperatures using math formula.
3. Control any watercooler that is supported by liquidctl.
4. Smooth transitions, averaging the last recorded temperature values.
5. Control GPU individual fans (for Nvidia compatible GPUs), monitoring temperature and calculating an optimal speed.
6. Control CPU clocking by changing the power plan based in key applications that may be running.
7. Control CPU clocking by changing the power plan based in limit of CPU temperatures.

## Installation

### Server-side configuration

#### Cronjob configuration (as root) for vega-server-root

On terminal, run:

> sudo crontab -e

In the editor that is opened, you can type this:

> @reboot /path/to/file/vega-server-root >> /path/to/file/vega-server-root.log 2>&1

- **@reboot:** this will start the script as soon Linux is loaded
- **/path/to/file/:** this is where the script is located
- **>>** this will append the output from the script to the vega-server-root.log
- **2>&1** this gets the standard output and the error output to the same log.

#### Startup configuration for vega-server-user

> sh -c "/path/to/file/vega-server-user >> /path/to/file/vega-server-user.log 2>&1"

#### Startup configuration for vega-server-gateway

> sh -c "/path/to/file/vega-server-gateway >> /path/to/file/vega-server-gateway.log 2>&1"

### Client-side configuration

Startup configuration for client-side app.

> sh -c "/path/to/file/vega-server-user >> /path/to/file/vega-server-user.log 2>&1"

## Package building

From root of the project:

### For Python Vega-server

> pyinstaller -F -n vega-server-gateway vega_server/gateway/main.py
> pyinstaller -F -n vega-server-root vega_server/rootspace/main.py
> pyinstaller -F -n vega-server-user vega_server/userspace/main.py

### For Python Vega-client

> pyinstaller -F -n vega-client vega_client/main.py

## Development

### Virtual environment

> sudo apt install python3.10-venv
> python -m venv vega_env
> source vega_env/bin/activate
> ./build_modules.sh

### Shared Library (vega_common)

The project uses a shared library called `vega_common` that centralizes common utilities used across different components of the system (rootspace, userspace, gateway, and client). This improves code reusability, maintainability, and consistency.

#### Library Structure

The library is organized as follows:

```plaintext
vega_common/
├── __init__.py        # Main package file with shortcuts to common functions
├── setup.py           # Installation configuration
└── utils/             # Utility modules
    ├── __init__.py
    ├── datetime_utils.py    # Date and time handling functions
    ├── files_manipulation.py # File I/O with enhanced error handling
    ├── list_process.py      # List manipulation utilities
    └── sub_process.py       # Shell command execution utilities
```

#### Library Installation

Install the shared library in development mode to automatically reflect changes in the library across all components:

```bash
# From the project root directory
pip install -e ./vega_common
```

#### Usage

You can use the shared library in two ways:

1. **Import specific utilities**:

   ```python
   from vega_common.utils.files_manipulation import read_file, write_file
   from vega_common.utils.list_process import list_average
   from vega_common.utils.datetime_utils import get_current_time
   ```

2. **Use shortcuts from the root package**:

   ```python
   from vega_common import read_file, list_average, get_current_time
   ```

#### Key Features

- **Improved Error Handling**: All functions include robust error handling with appropriate exceptions
- **Type Hints**: Full Python type annotations for better IDE integration and type checking
- **Documentation**: Comprehensive docstrings for all functions and modules
- **Consistent API**: Uniform interface design across all utility modules

#### Migration from Legacy Utilities

When migrating existing code to use vega_common:

1. Replace imports like `from utils.filesManipulation import read_file` with `from vega_common.utils.files_manipulation import read_file`
2. Replace imports like `from utils.listProcess import list_average` with `from vega_common.utils.list_process import list_average`
3. Replace imports like `from utils.datetime import get_current_time` with `from vega_common.utils.datetime_utils import get_current_time`

A migration script is available to automatically update imports across the codebase (see `tools/update_imports.py`).
