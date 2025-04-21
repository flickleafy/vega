#!/usr/bin/env python3
"""
Vega Build Script - Python equivalent of build.sh

This script builds all Vega executables using PyInstaller, creates the distribution
folder structure, and generates the installer script.
"""

import os
import sys
import shutil
import stat
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Constants
BUILD_DIR_NAME = "dist"


def run_command(cmd: List[str]) -> Tuple[bool, str]:
    """
    Run a shell command and return its success status and output.

    Args:
        cmd: Command to execute as a list of strings

    Returns:
        Tuple containing (success_boolean, command_output)

    Time complexity: O(P) where P is the process execution time
    """
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, str(e)


def build_executable(name: str, script_path: str) -> bool:
    """
    Build an executable using PyInstaller.

    Args:
        name: Name for the output executable
        script_path: Path to the Python script to compile

    Returns:
        Boolean indicating success or failure

    Time complexity: O(P) where P is the PyInstaller process execution time
    """
    print(f"Building {name}...")
    success, output = run_command(["pyinstaller", "-F", "-n", name, script_path])

    if not success:
        print(f"Error building {name}:")
        print(output)

    return success


def create_installer_script(build_dir: Path) -> bool:
    """
    Copy the installer script from assets/installer.py to the build directory and make it executable.

    Args:
        build_dir: Path to the build directory

    Returns:
        Boolean indicating success or failure

    Time complexity: O(1) for copying a single file
    """
    installer_src = Path(__file__).parent / "assets" / "installer.py"
    installer_dest = build_dir / "installer.py"

    print(f"Copying installer script from {installer_src} to {installer_dest}...")

    try:
        # Ensure source file exists
        if not installer_src.exists():
            print(f"Error: Installer script source not found at {installer_src}")
            return False

        # Copy the installer script
        shutil.copy2(installer_src, installer_dest)

        # Make the installer script executable
        os.chmod(installer_dest, os.stat(installer_dest).st_mode | stat.S_IEXEC)

        # Create a simple shell script wrapper to invoke the Python installer
        wrapper_path = build_dir / "installer.sh"
        with open(wrapper_path, "w") as f:
            f.write("#!/bin/bash\n\n")
            f.write("# Wrapper script to launch the Python installer\n\n")
            f.write('SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n\n')
            f.write("# Find Python interpreter\n")
            f.write('PYTHON_CMD="python3"\n')
            f.write("if ! command -v $PYTHON_CMD &> /dev/null; then\n")
            f.write('    PYTHON_CMD="python"\n')
            f.write("    if ! command -v $PYTHON_CMD &> /dev/null; then\n")
            f.write(
                '        echo "Error: Python interpreter not found. Please install Python 3."\n'
            )
            f.write("        exit 1\n")
            f.write("    fi\n")
            f.write("fi\n\n")
            f.write("# Execute the Python installer\n")
            f.write('exec $PYTHON_CMD "$SCRIPT_DIR/installer.py" "$@"\n')

        # Make the wrapper script executable too
        os.chmod(wrapper_path, os.stat(wrapper_path).st_mode | stat.S_IEXEC)

        return True
    except Exception as e:
        print(f"Error copying installer script: {e}")
        return False


def main() -> int:
    """
    Main build function - coordinates the build process.

    Returns:
        Exit code (0 for success, non-zero for failure)

    Time complexity: O(P) where P is the sum of all process execution times
    """
    # Get script directory
    script_dir = Path(__file__).parent.absolute()
    build_dir = script_dir / BUILD_DIR_NAME
    assets_dir = script_dir / "assets"

    # Dictionary of executables to build: {name: script_path}
    executables = {
        "vega-server-gateway": "vega_server/gateway/main.py",
        "vega-server-root": "vega_server/rootspace/main.py",
        "vega-server-user": "vega_server/userspace/main.py",
        "vega-client": "vega_client/main.py",
    }

    # Ensure build directory exists
    build_dir.mkdir(exist_ok=True)

    # Build all executables
    print("Building executables...")
    build_failures = 0

    for name, script_path in executables.items():
        if not build_executable(name, str(script_dir / script_path)):
            build_failures += 1

    if build_failures > 0:
        print(f"Failed to build {build_failures} executable(s).")
        return 1

    # Copy assets (.desktop files)
    print("Copying assets to dist folder...")
    try:
        if assets_dir.exists():
            for desktop_file in assets_dir.glob("*.desktop"):
                shutil.copy2(desktop_file, build_dir)
        else:
            print(
                f"Warning: Assets directory {assets_dir} not found. Skipping desktop files."
            )
    except Exception as e:
        print(f"Error copying assets: {e}")
        return 1

    # Create icons directory
    icons_dir = build_dir / "icons"
    icons_dir.mkdir(exist_ok=True)

    # Copy icon if it exists
    icon_path = script_dir / "vega_client" / "cpu_v.png"
    if icon_path.is_file():
        try:
            shutil.copy2(icon_path, icons_dir / "vega-icon.png")
        except Exception as e:
            print(f"Error copying icon: {e}")
            return 1

    # Create installer script
    if not create_installer_script(build_dir):
        return 1

    print(f"Build complete! Installer created at {build_dir}/installer.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
