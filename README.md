# VEGA - Dynamic cooling, lighting and clocking controller

A dynamic cooling (watercooler, cpu, and gpu) controller, dynamic lighting controller (any device supported by openRGB), and dynamic cpu clocking controller. Should work in any Linux that supports the project dependencies.

## Dependencies

It uses [liquidctl](https://github.com/liquidctl/liquidctl) as its basis for the watercooler controlling.\
It uses [openRGB](https://gitlab.com/CalcProgrammer1/OpenRGB) for ligthing controlling for RAM, Motherboard, and couple other devices supported by openRGB.\
It uses [nvidia-settings](_)/[nvidia-ml-py](https://pypi.org/project/nvidia-ml-py/) to controll gpu temperature and fans, and in the future, it is planned to controll other GPU parameters.

### System Dependencies

Before installing Python packages, you need to install these system dependencies:

```bash
sudo apt-get update
sudo apt-get install -y \
  libusb-1.0-0-dev \
  libudev-dev \
  libcairo2-dev \
  pkg-config \
  python3-dev \
  libgirepository1.0-dev \
  gir1.2-gtk-3.0 \
  libcairo2 \
  libglib2.0-dev \
  gobject-introspection \
  python3-gi \
  python3-cairo
```

These dependencies are required for:

- **libgirepository1.0-dev** & **gobject-introspection**: GObject introspection development files needed for PyGObject
- **libcairo2-dev** & **libcairo2**: Cairo graphics library needed for PyGObject
- **libglib2.0-dev**: GLib development files for PyGObject
- **gir1.2-gtk-3.0**: GTK bindings for Python
- **pkg-config**: Required for detecting installed libraries
- **python3-dev**: Python development headers for building extensions
- **libusb-1.0-0-dev** & **libudev-dev**: Required for liquidctl hardware access

### Installing Python Dependencies

The project dependencies are managed through a requirements.txt file. To install all required packages:

```bash
# Activate your virtual environment first (if using one)
pip install -r requirements.txt
pip install -e ./vega_common
```

More details for venvs in the "Virtual environment" section
This will install all runtime dependencies as well as development tools needed for testing and code quality checks.

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

> @reboot VEGA_USER_HOME=/home/xxx /path/to/file/vega-server-root

- **VEGA_USER_HOME=/home/xxx:** sets the user's home directory so logs are stored in `/home/xxx/.config/vega_suit/` instead of `/root/.config/vega_suit/`. Replace `xxx` with your actual username.
- **@reboot:** this will start the script as soon Linux is loaded
- **/path/to/file/:** this is where the script is located
- **>>** this will append the output from the script to the vega-server-root.log
- **2>&1** this gets the standard output and the error output to the same log.

#### Startup configuration for vega-server-user

> sh -c "/path/to/file/vega-server-user"

#### Startup configuration for vega-server-gateway

> sh -c "/path/to/file/vega-server-gateway"

### Client-side configuration

Startup configuration for client-side app.

> sh -c "/path/to/file/vega-client"

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

```bash
# Install Python venv package
sudo apt install python3.10-venv

# Create virtual environment
python -m venv vega_env

# Activate virtual environment
source vega_env/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e ./vega_common

# Build modules
./build_modules.sh
```

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
    ├── color_utils.py        # Color manipulation and conversion functions
    ├── datetime_utils.py     # Date and time handling functions
    ├── files_manipulation.py # File I/O with enhanced error handling
    ├── list_process.py       # List manipulation utilities
    ├── sub_process.py        # Shell command execution utilities
    └── temperature_utils.py  # Temperature conversion and calculation functions
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
   from vega_common.utils.color_utils import rgb_to_hsv, hex_to_rgb
   from vega_common.utils.temperature_utils import celsius_to_fahrenheit
   ```

2. **Use shortcuts from the root package**:

   ```python
   from vega_common import read_file, list_average, get_current_time, rgb_to_hsv, celsius_to_fahrenheit
   ```

#### Key Features

- **Improved Error Handling**: All functions include robust error handling with appropriate exceptions
- **Type Hints**: Full Python type annotations for better IDE integration and type checking
- **Documentation**: Comprehensive docstrings for all functions and modules
- **Consistent API**: Uniform interface design across all utility modules
- **Color Manipulation**: Standardized functions for color format conversion and manipulation
- **Temperature Processing**: Unified temperature conversion and fan speed calculation utilities

#### Utility Modules Highlights

##### Color Utilities

```python
# Convert between color formats (RGB, HSV, HEX)
rgb_color = [255, 0, 0]  # Red
hsv_color = rgb_to_hsv(rgb_color)  # [0, 100, 100]
hex_color = rgb_to_hex(255, 0, 0)  # "#ff0000"

# Color manipulation
shifted_color = shift_hue(hsv_color.copy(), 120)  # Shift hue by 120 degrees
brighter_color = adjust_brightness(hsv_color.copy(), 10)  # Increase brightness
```

##### Temperature Utilities

```python
# Temperature conversion
fahrenheit = celsius_to_fahrenheit(30)  # 86.0

# Fan speed calculations based on temperature
fan_speed = calculate_safe_fan_speed(
    current_temp=70,  # CPU temperature in Celsius
    min_temp=40,      # Minimum temperature threshold 
    max_temp=85,      # Maximum temperature threshold
    min_speed=30,     # Minimum fan speed percentage
    max_speed=100     # Maximum fan speed percentage
)  # Returns appropriate fan speed percentage
```

#### Compatibility Layers

To maintain backward compatibility during the migration to vega_common, compatibility layers have been created in both rootspace and userspace components:

```
vega_server/rootspace/utils/
├── colorUtils.py         # Re-exports color functions from vega_common
├── listProcess.py        # Re-exports list functions from vega_common
├── temperatureUtils.py   # Re-exports temperature functions from vega_common
└── ...

vega_server/userspace/utils/
├── colorUtils.py         # Re-exports color functions from vega_common
├── listProcess.py        # Re-exports list functions from vega_common
├── temperatureUtils.py   # Re-exports temperature functions from vega_common
└── ...
```

These compatibility layers allow existing code to continue functioning while components are gradually migrated to use the common utilities directly.

#### Migration from Legacy Utilities

When migrating existing code to use vega_common:

1. Replace imports like `from utils.filesManipulation import read_file` with `from vega_common.utils.files_manipulation import read_file`
2. Replace imports like `from utils.listProcess import list_average` with `from vega_common.utils.list_process import list_average`
3. Replace imports like `from utils.datetime import get_current_time` with `from vega_common.utils.datetime_utils import get_current_time`

A migration script is available to automatically update imports across the codebase (see `tools/update_imports.py`).

### Automated Testing

The project uses pytest as the testing framework with additional tools for code coverage and quality assurance.

#### Running Tests

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests for a specific module
pytest tests/vega_common/utils/test_datetime_utils.py

# Run tests with coverage analysis
pytest --cov=vega_common --cov-report=term-missing
```

#### Automated Test Scripts

For convenience, several test automation scripts are available:

```bash
# Run basic test suite
./scripts/run_tests.sh

# Run tests with coverage analysis
./scripts/run_coverage.sh

# Run code quality checks (flake8, mypy)
./scripts/run_quality_checks.sh
```

#### Code Quality Checks

To run code quality checks manually:

```bash
# Run static type checking
mypy vega_common vega_server vega_client

# Run style and error checks
flake8 vega_common vega_server vega_client
```

### Continuous Integration

The project uses GitHub Actions for continuous integration. Every commit triggers the following automated checks:

1. **Unit Tests**: All test cases are run to ensure functionality
2. **Code Coverage**: Coverage reports are generated to track test coverage
3. **Type Checking**: Static type analysis with mypy
4. **Code Quality**: Style and error checking with flake8

The CI configuration can be found in `.github/workflows/ci.yml` file.

When contributing to the project, make sure all CI checks pass before submitting pull requests.
