#!/usr/bin/env python3
"""
Vega Application Installer Script

This script installs the Vega application, including:
- Installing executables
- Setting up desktop entries
- Configuring autostart services
- Creating systemd service for root component (if system-wide install)

The installer supports both system-wide and user-only installation modes.
"""

import os
import sys
import shutil
import stat
import subprocess
import getpass
from pathlib import Path


class VegaInstaller:
    """
    Handles installation of Vega application components.

    This class manages the entire installation process, including path setup,
    directory creation, executable installation, desktop entry creation,
    and service configuration.

    Time complexity: Overall O(N) where N is the number of files to install,
    assuming constant time for most file operations.
    """

    def __init__(self):
        """Initialize the installer with default paths and settings."""
        # Get the directory where the installer script is located
        self.installer_dir = Path(os.path.dirname(os.path.abspath(__file__)))

        # Define system-wide installation paths (require sudo)
        self.system_bin_dir = Path("/usr/local/bin/vega_suit")
        self.system_app_dir = Path("/usr/local/share/vega_suit")
        self.system_apps_dir = Path("/usr/share/applications")
        self.system_icons_dir = Path("/usr/share/icons/hicolor/256x256/apps")

        # Define user-specific installation paths
        home = Path.home()
        self.user_bin_dir = home / ".local/bin/vega_suit"
        self.user_app_dir = home / ".local/share/vega_suit"
        self.user_apps_dir = home / ".local/share/applications"
        self.user_icons_dir = home / ".local/share/icons"

        # Common directories
        self.autostart_dir = home / ".config/autostart"
        self.config_dir = home / ".config/vega_suit"
        self.desktop_dir = home / "Desktop"

        # Selected installation paths (to be set based on installation type)
        self.bin_dir = None
        self.app_dir = None
        self.apps_dir = None
        self.icons_dir = None

        # Installation type (0 = user, 1 = system)
        self.system_install = 0

    def check_sudo_access(self) -> bool:
        """
        Check if the current user has sudo access.

        Returns:
            bool: True if the user has sudo access, False otherwise.

        Time complexity: O(1) - single subprocess call
        """
        try:
            # Try running sudo with -n (non-interactive) to see if we have sudo access
            result = subprocess.run(
                ["sudo", "-n", "true"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=2,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def ask_for_system_install(self) -> bool:
        """
        Ask the user if they want to perform a system-wide installation.

        Returns:
            bool: True if the user chose system-wide installation, False otherwise.

        Time complexity: O(1) - simple I/O operation
        """
        print(
            "Sudo access available. Would you like to install Vega system-wide? (y/n)"
        )
        while True:
            choice = input().strip().lower()
            if choice in ["y", "yes"]:
                return True
            elif choice in ["n", "no"]:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")

    def setup_installation_type(self):
        """
        Determine installation type (system-wide or user-only) based on sudo access.

        Time complexity: O(1) - simple condition checks and assignments
        """
        has_sudo = self.check_sudo_access()

        if has_sudo:
            system_install = self.ask_for_system_install()
            self.system_install = 1 if system_install else 0
            if system_install:
                print("Proceeding with system-wide installation.")
            else:
                print("Proceeding with user-only installation.")
        else:
            self.system_install = 0
            print("No sudo access detected. Proceeding with user-only installation.")

        # Set installation directories based on install type
        if self.system_install:
            self.bin_dir = self.system_bin_dir
            self.app_dir = self.system_app_dir
            self.apps_dir = self.system_apps_dir
            self.icons_dir = self.system_icons_dir
        else:
            self.bin_dir = self.user_bin_dir
            self.app_dir = self.user_app_dir
            self.apps_dir = self.user_apps_dir
            self.icons_dir = self.user_icons_dir

    def create_directories(self):
        """
        Create all necessary directories for the installation.

        Time complexity: O(1) - fixed number of directories
        """
        print("Creating installation directories...")
        os.makedirs(self.bin_dir, exist_ok=True)
        os.makedirs(self.app_dir, exist_ok=True)
        os.makedirs(self.apps_dir, exist_ok=True)
        os.makedirs(self.icons_dir, exist_ok=True)
        os.makedirs(self.autostart_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(
            Path.home() / ".local/share/vega_suit", exist_ok=True
        )  # Log directory

    def install_executables(self):
        """
        Install the Vega executables to the appropriate directory.

        Time complexity: O(1) - fixed number of executables
        """
        print(f"Installing Vega executables to {self.bin_dir}...")
        executables = [
            "vega-client",
            "vega-server-gateway",
            "vega-server-user",
            "vega-server-root",
        ]

        for exe in executables:
            src_path = Path(self.installer_dir) / exe
            dst_path = self.bin_dir / exe

            if self.system_install:
                self._run_sudo_command(
                    ["install", "-m", "755", str(src_path), str(dst_path)]
                )
            else:
                # Copy the file
                shutil.copy2(src_path, dst_path)
                # Set permissions (executable)
                os.chmod(
                    dst_path,
                    os.stat(dst_path).st_mode
                    | stat.S_IXUSR
                    | stat.S_IXGRP
                    | stat.S_IXOTH,
                )

    def install_icons(self):
        """
        Install the application icons.

        Time complexity: O(1) - single icon file
        """
        print("Installing icons...")
        icon_dir = Path(self.installer_dir) / "icons"

        if icon_dir.exists():
            src_icon = icon_dir / "vega-icon.png"
            dst_icon = self.icons_dir / "vega-icon.png"

            if self.system_install:
                self._run_sudo_command(
                    ["install", "-m", "644", str(src_icon), str(dst_icon)]
                )
            else:
                shutil.copy2(src_icon, dst_icon)

    def create_desktop_entry(self):
        """
        Create desktop entry for the Vega client application.

        Time complexity: O(1) - single desktop entry file
        """
        print("Creating application menu entry...")
        desktop_content = f"""[Desktop Entry]
Type=Application
Name=Vega Client
Comment=Vega Client Application
Exec={self.bin_dir}/vega-client
Icon=vega-icon
Terminal=false
Categories=Utility;System;
"""

        # Write to applications directory
        apps_entry_path = self.apps_dir / "vega-client.desktop"
        if self.system_install:
            self._run_sudo_command(
                [
                    "bash",
                    "-c",
                    f"cat > {apps_entry_path} << 'EOT'\n{desktop_content}EOT\n",
                ]
            )
        else:
            with open(apps_entry_path, "w") as f:
                f.write(desktop_content)

        # Write to desktop
        desktop_entry_path = self.desktop_dir / "vega-client.desktop"
        with open(desktop_entry_path, "w") as f:
            f.write(desktop_content)
        # Make executable
        os.chmod(desktop_entry_path, os.stat(desktop_entry_path).st_mode | stat.S_IXUSR)

    def setup_autostart_services(self):
        """
        Configure services to start automatically on boot.

        Time complexity: O(1) - fixed number of service files
        """
        print("Setting up autostart services...")

        # Gateway service
        gateway_content = f"""[Desktop Entry]
Type=Application
Exec=sh -c "{self.bin_dir}/vega-server-gateway >> $HOME/.local/share/vega_suit/vega-server-gateway.log 2>&1"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Vega Server Gateway
Comment=Vega Server Gateway background service
"""
        with open(self.autostart_dir / "vega-server-gateway.desktop", "w") as f:
            f.write(gateway_content)

        # User service
        user_content = f"""[Desktop Entry]
Type=Application
Exec=sh -c "{self.bin_dir}/vega-server-user >> $HOME/.local/share/vega_suit/vega-server-user.log 2>&1"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Vega Server User
Comment=Vega Server User background service
"""
        with open(self.autostart_dir / "vega-server-user.desktop", "w") as f:
            f.write(user_content)

    def setup_root_service(self):
        """
        Set up the root service as a systemd service.

        Time complexity: O(1) for file creation, O(P) for systemctl operations
        where P is the process execution time.
        """
        if self.system_install:
            print("Setting up root service as a systemd service...")
            service_content = f"""[Unit]
Description=Vega Server Root Service
After=network.target

[Service]
ExecStart={self.bin_dir}/vega-server-root
Restart=on-failure
User=root

[Install]
WantedBy=multi-user.target
"""
            service_file = "/etc/systemd/system/vega-server-root.service"

            # Create service file
            self._run_sudo_command(
                ["bash", "-c", f"cat > {service_file} << 'EOT'\n{service_content}EOT\n"]
            )

            # Enable and start the service
            self._run_sudo_command(["systemctl", "daemon-reload"])
            self._run_sudo_command(["systemctl", "enable", "vega-server-root.service"])
            self._run_sudo_command(["systemctl", "start", "vega-server-root.service"])

            print("Root service installed and started as a systemd service.")
        else:
            print(
                "Warning: Without system-wide installation, the root service cannot be properly set up as a systemd service."
            )
            print(
                f"The root service will be available at {self.bin_dir}/vega-server-root but will need to be run manually with sudo privileges."
            )
            print("")
            print(
                "To properly install the root service, you may run the following commands later with sudo privileges:"
            )
            print(f'sudo cp "{self.bin_dir}/vega-server-root" /usr/local/bin/')
            print(
                "sudo bash -c 'cat > /etc/systemd/system/vega-server-root.service << EOT"
            )
            print("[Unit]")
            print("Description=Vega Server Root Service")
            print("After=network.target")
            print("")
            print("[Service]")
            print("ExecStart=/usr/local/bin/vega-server-root")
            print("Restart=on-failure")
            print("User=root")
            print("")
            print("[Install]")
            print("WantedBy=multi-user.target")
            print("EOT'")
            print("sudo systemctl daemon-reload")
            print("sudo systemctl enable vega-server-root.service")
            print("sudo systemctl start vega-server-root.service")

    def _run_sudo_command(self, cmd_list):
        """
        Helper method to run a command with sudo.

        Args:
            cmd_list (list): Command to run as a list of strings.

        Returns:
            bool: True if command succeeded, False otherwise.

        Time complexity: O(P) where P is the process execution time
        """
        try:
            cmd = ["sudo"] + cmd_list
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error running command with sudo: {e}")
            return False

    def run_installation(self):
        """
        Run the complete installation process.

        Time complexity: Sum of individual steps,
        dominated by the system commands in system-wide installation.
        """
        print("Vega Application Installer")
        print("==========================")
        print("")

        self.setup_installation_type()
        print("Installing Vega application...")

        self.create_directories()
        self.install_executables()
        self.install_icons()
        self.create_desktop_entry()
        self.setup_autostart_services()
        self.setup_root_service()

        print("")
        print("Installation complete!")
        print(
            "You can find the Vega Client in your applications menu and on your desktop."
        )
        print(
            "Background services have been configured to start automatically at system boot."
        )
        print("Logs will be stored in $HOME/.local/share/vega/")


def main():
    """
    Main function to run the Vega installer.

    Time complexity: Same as VegaInstaller.run_installation()
    """
    try:
        installer = VegaInstaller()
        installer.run_installation()
        return 0
    except KeyboardInterrupt:
        print("\nInstallation canceled.")
        return 1
    except Exception as e:
        print(f"Error during installation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
