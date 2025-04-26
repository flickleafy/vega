# Changelog

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
