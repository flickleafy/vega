# Changelog

## Apr 29 2025

### Global
- **Centralized Logging System**:
  - Replaced all `print()` statements with structured `logger` calls across the codebase
  - Added `get_module_logger()` function for per-module log files with daily rotation and 30-day retention
  - Logs stored in `~/.config/vega_suit/<module>/` with hierarchical organization
  - Added `VEGA_USER_HOME` environment variable support to ensure rootspace logs go to user's config directory instead of `/root/`
  - Supports `SUDO_USER` and `PKEXEC_UID` detection for automatic user directory resolution
  - Graceful fallback to console-only logging when file logging fails due to permissions
- **Build System**:
  - Updated `build.py` to bundle the taskbar icon (`cpu_v.png`) inside the `vega-client` executable using PyInstaller's `--add-data`
  - Added support for per-executable extra build arguments
- **Documentation**:
  - Simplified startup configuration examples in `README.md` (removed log redirection, now handled by centralized logging)
  - Updated crontab and systemd service examples to include `VEGA_USER_HOME` setting
- **Installer**:
  - Updated `installer.py` to automatically set `VEGA_USER_HOME` in systemd service files
  - Added user-friendly messages about log storage locations
  - Improved manual installation instructions with `VEGA_USER_HOME` guidance
- **Desktop Files**:
  - Updated `sh-2.desktop` and `sudo.desktop` to remove log redirection (now handled by centralized logging)

### vega_common
- **CPU Power Management**:
  - Added new `CpuPowerPlanManager` class for centralized CPU power plan control
  - Implemented `PowerPlan` enum with `PERFORMANCE`, `BALANCED_PERFORMANCE`, `BALANCED_EFFICIENT`, `POWERSAVE` modes
  - Added `GovernorSetting` enum for physical Linux kernel governors
  - Added `EnergyPerformancePreference` (EPP) enum for driver-specific power hints (amd-pstate-epp, intel_pstate)
  - Intelligent mapping of logical power plans to available governors and EPP settings
  - Added `cpu_thermal_specs.py` with thermal specifications for various AMD CPU models
  - Added comprehensive test suite `test_cpu_powerplan_manager.py`
- **Process Management**:
  - Added new `ProcessPriorityManager` class for unified process priority control
- **Device Monitoring**:
  - Enhanced `cpu_devices.py` with improved CPU controller implementation using `CpuPowerPlanManager`
  - Updated `gpu_devices.py` with expanded GPU monitoring and thermal protection capabilities
  - Added `apply_thermal_protection()` method to `NvidiaGpuController` for dynamic power limiting based on temperature
  - Added support for GPUs with 3 fans in `set_fan_speed()` method
  - Improved `watercooler_devices.py` error handling
  - Enhanced `device_monitor.py` with better status tracking
- **Utilities**:
  - Updated `color_gradient_utils.py`, `files_manipulation.py`, `list_process.py`, `sub_process.py`, `process_utils.py` with centralized logging
- **Tests**:
  - Fixed `test_device_monitoring.py` to match updated DeviceManager API (`get_all_statuses`, `get_device_status`)
  - Fixed `test_color_utils.py` to handle OpenRGBColor return type from `rgb_to_rgbcolor`
  - Fixed `test_gpu_devices_gpu_controller.py` for single-value tuple fan speed (now valid)
  - Fixed `test_gpu_devices_gpu_monitor.py` to patch `logger` instead of deprecated `logging` module
  - Updated `test_cpu_devices_cpu_controller.py` for new CPU controller implementation with `LOGICAL_POWER_PLANS`

### vega_server/gateway
- **Client Connections**:
  - Updated `client_connection.py`, `ctRootThread.py`, `ctUserThread.py` with centralized logging
- **Server**:
  - Updated `alternative_start_server.py` and `start_server.py` with centralized logging

### vega_server/userspace
- **Watercooler**:
  - Refactored `wcThread.py` with improved architecture
  - Removed deprecated utility modules: `cpuDegreeToSpeed.py`, `cpuStatus.py`, `wcStatus.py`, `wcTemp.py`
- **Lighting**:
  - Updated `lightingStatus.py` and `lightingThread.py` with centralized logging
- **Server**:
  - Updated `start_server.py` with centralized logging
- **Utilities**:
  - Removed deprecated modules: `colorUtils.py`, `listProcess.py`, `temperatureUtils.py` (functionality moved to `vega_common`)

### vega_server/rootspace
- **CPU Clocking**:
  - Refactored `cpuClockingThread.py` to use new `CpuPowerPlanManager`
  - Removed deprecated modules: `cpuGetPowerPlan.py`, `cpuPowerPlanSwitcher.py`, `cpuSetPowerPlan.py`, `detectBalance.py`, `detectPerformance.py`
- **GPU Cooling**:
  - Updated `gpuThread.py` with improved GPU monitoring and thermal protection integration
  - Added support for 3-fan GPUs with independent speed control (`speed_fan1`, `speed_fan2`, `speed_fan3`)
  - Integrated `apply_thermal_protection()` for dynamic power limit adjustment when approaching Tjmax
  - Updated `gpuDisplay.py` and `multiscreens.py` with centralized logging
- **Server**:
  - Updated `start_server.py` with centralized logging
- **Utilities**:
  - Removed deprecated modules: `colorUtils.py`, `listProcess.py`, `processList.py`, `temperatureUtils.py` (functionality moved to `vega_common`)

### vega_client
- **Client Connection**:
  - Updated `client_connection.py` and `ctThread.py` with centralized logging
- **Taskbar**:
  - Added `get_icon_path()` function to handle icon resolution for both development and PyInstaller bundled scenarios
  - Uses `sys._MEIPASS` detection for bundled executable support


## Apr 25 2025

### Global
- **Build & Deployment Automation**:
  - Added shell scripts for streamlined development workflow: `setup_venv.sh`, `activate.sh`, `build_vega.sh`
  - Enhanced `build.py` with PyInstaller improvements

### vega_common
- **Device Monitoring**:
  - Integrated `CpuMonitor` for comprehensive CPU status tracking
  - **Watercooler Monitoring & Control**:
    - Refactored monitoring to use new `WatercoolerMonitor` and `WatercoolerController` classes
    - Implemented intelligent device filtering to exclude LED-only controllers (e.g., Hue, Smart Device) from watercooler detection
    - Added comprehensive exception handling across all device operations to prevent crashes
    - Implemented fallback logic for establishing connection and initialization
    - Added support for multiple lighting modes ("fixed", "static", "super-fixed", etc.) with auto-retry
  - Enhanced device status error handling with `has_error()` method
  - **Color Management**:
    - Extracted temperature-to-color calculation into reusable `get_temperature_color()` utility
    - Added compatibility layer for OpenRGB's `RGBColor` object in `color_utils.py`
  - **Core Utilities**:
    - Enhanced `DeviceStatus` to support human-readable device names and error tracking (`update_property`, `mark_updated`)
    - Improved `DeviceMonitor` to facilitate status tracking and property registration
    - Added specific `PermissionError` handling in `sub_process.py` for subprocess execution errors

### vega_server/userspace
- **Watercooler & Lighting**:
  - Refactored color signature tracking to support **per-device tracking** using device memory addresses as keys (in `globals.py`)
  - Changed `COLOR_SIG_LAST` from single value to dictionary-based storage
  - Improved color change detection to prevent unnecessary LED updates across multiple devices
  - Added specific initialization handling for GPUs (switching modes to ensure color changes work)
  - Removed unused `liquidctl.cli` imports, using direct `find_liquidctl_devices()` instead
  - Improved logging and error messages throughout watercooler thread
- **Core**:
  - Added shebang and proper docstrings to `main.py`
  - Enhanced path handling for proper module resolution

### vega_server/rootspace
- **GPU Monitoring**:
  - Standardized GPU IDs to use numerical indices (0, 1) instead of PCI bus IDs
