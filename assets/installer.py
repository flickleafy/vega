#!/usr/bin/env python3
"""
Vega Application Installer Script

This script installs the Vega application, including:
- Verifying and installing system dependencies
- Installing executables
- Setting up desktop entries
- Configuring autostart services
- Creating systemd service for root component (if system-wide install)
- Managing $PATH for user installs
- Checking hardware-specific prerequisites (NVIDIA, i2c-dev, liquidctl udev)
- Logging everything to ~/.config/vega_suit/install.log

The installer supports both system-wide and user-only installation modes,
as well as an --uninstall mode to cleanly remove the application.
"""

import argparse
import datetime
import json
import logging
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

VERSION = "2.1.0"

EXECUTABLES = [
    "vega-client",
    "vega-server-gateway",
    "vega-server-user",
    "vega-server-root",
]

# System packages required for Vega to run.
# Each entry is (package_name, human_description, is_critical).
REQUIRED_SYSTEM_PACKAGES = [
    ("libusb-1.0-0", "USB device access (liquidctl watercooler control)", True),
    ("libhidapi-libusb0", "HID device access for watercoolers", True),
    ("libcairo2", "Cairo graphics library (GTK client)", True),
    ("libgirepository1.0-dev", "GObject introspection (GTK client)", True),
    ("gir1.2-gtk-3.0", "GTK 3 bindings (client tray application)", True),
    ("gir1.2-appindicator3-0.1", "AppIndicator3 for system tray (client)", True),
    ("gir1.2-notify-0.7", "Desktop notifications (client)", True),
    ("python3-gi", "Python GObject introspection bindings", True),
    ("python3-cairo", "Python Cairo bindings", True),
    ("libglib2.0-0", "GLib library", True),
]

# Optional packages — warn if missing but don't block installation.
OPTIONAL_SYSTEM_PACKAGES = [
    ("lm-sensors", "Hardware sensor monitoring (CPU temperature)"),
]

# NVIDIA packages — mandatory only when an NVIDIA GPU is detected.
NVIDIA_PACKAGES = [
    ("nvidia-xconfig", "NVIDIA X config tool (required for GPU fan control)"),
]

# Manifest file tracking every file the installer creates/modifies.
MANIFEST_FILENAME = ".vega_install_manifest.json"


# ──────────────────────────────────────────────────────────────────────────────
# Installer Class
# ──────────────────────────────────────────────────────────────────────────────


class VegaInstaller:
    """
    Handles installation and uninstallation of Vega application components.

    This class manages the entire installation process, including dependency
    verification, path setup, directory creation, executable installation,
    desktop entry creation, service configuration, and clean uninstallation.
    """

    def __init__(self, dry_run: bool = False, log_path: Optional[str] = None):
        """Initialize the installer with default paths and settings.

        Args:
            dry_run: If True, print actions without modifying the system.
            log_path: Optional path for the install log file.
        """
        self.installer_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.home = Path.home()
        self.dry_run: bool = dry_run

        # System-wide installation paths
        self.system_bin_dir = Path("/usr/local/bin/vega_suit")
        self.system_app_dir = Path("/usr/local/share/vega_suit")
        self.system_apps_dir = Path("/usr/share/applications")
        self.system_icons_dir = Path("/usr/share/icons/hicolor/256x256/apps")

        # User-specific installation paths
        self.user_bin_dir = self.home / ".local/bin/vega_suit"
        self.user_app_dir = self.home / ".local/share/vega_suit"
        self.user_apps_dir = self.home / ".local/share/applications"
        self.user_icons_dir = self.home / ".local/share/icons"

        # Common directories
        self.autostart_dir = self.home / ".config/autostart"
        self.config_dir = self.home / ".config/vega_suit"
        self.desktop_dir = self._get_desktop_dir()

        # Selected installation paths (set later)
        self.bin_dir: Optional[Path] = None
        self.app_dir: Optional[Path] = None
        self.apps_dir: Optional[Path] = None
        self.icons_dir: Optional[Path] = None

        self.system_install: bool = False
        self.errors: List[str] = []
        self.installed_files: List[str] = []
        self.installed_dirs: List[str] = []

        # File-based logging
        self._file_logger = self._setup_file_logging(log_path)

    # ── file logging ──────────────────────────────────────────────────────

    def _setup_file_logging(self, log_path: Optional[str] = None) -> logging.Logger:
        """Configure a file logger that persists all installer output."""
        logger = logging.getLogger("vega_installer")
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()

        log_file = Path(log_path) if log_path else self.config_dir / "install.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        handler = logging.FileHandler(str(log_file), mode="a", encoding="utf-8")
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(handler)

        logger.info("=" * 60)
        logger.info(f"Vega Installer v{VERSION} — session started")
        logger.info(f"Dry-run: {self.dry_run}")
        logger.info(f"System: {sys.platform}, Python {sys.version}")
        logger.info(f"Log file: {log_file}")
        logger.info("=" * 60)
        return logger

    def _log(self, message: str, level: str = "info"):
        """Print to console AND write to the install log file."""
        print(message)
        getattr(self._file_logger, level, self._file_logger.info)(message.lstrip(" "))

    # ── helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _get_desktop_dir() -> Path:
        """Get the user's desktop directory using xdg-user-dir, with fallback."""
        try:
            result = subprocess.run(
                ["xdg-user-dir", "DESKTOP"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, timeout=3,
            )
            if result.returncode == 0 and result.stdout.strip():
                return Path(result.stdout.strip())
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return Path.home() / "Desktop"

    def _record_file(self, path: Path):
        """Record a file that was created during installation."""
        self.installed_files.append(str(path))

    def _record_dir(self, path: Path):
        """Record a directory that was created during installation."""
        self.installed_dirs.append(str(path))

    def _add_error(self, message: str):
        """Accumulate a non-fatal error for end-of-run reporting."""
        self.errors.append(message)
        self._log(f"  ⚠ {message}", "warning")

    def _run_sudo_command(self, cmd_list: List[str], description: str = "") -> bool:
        """Run a command with sudo, accumulating errors on failure."""
        if self.dry_run:
            self._log(f"  [DRY-RUN] sudo {' '.join(cmd_list)}")
            return True
        try:
            cmd = ["sudo"] + cmd_list
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError as e:
            msg = f"sudo command failed{f' ({description})' if description else ''}: {e}"
            self._add_error(msg)
            return False

    def _safe_makedirs(self, path: Path, sudo: bool = False):
        """Create directory (recording it), with optional sudo."""
        if path.exists():
            return
        if self.dry_run:
            self._log(f"  [DRY-RUN] mkdir -p {path}")
            self._record_dir(path)
            return
        if sudo:
            self._run_sudo_command(
                ["mkdir", "-p", str(path)], description=f"create directory {path}"
            )
        else:
            path.mkdir(parents=True, exist_ok=True)
        self._record_dir(path)

    # ── manifest persistence ──────────────────────────────────────────────

    def _manifest_path(self) -> Path:
        return self.config_dir / MANIFEST_FILENAME

    def _save_manifest(self):
        """Persist the list of installed files/dirs plus settings."""
        manifest = {
            "version": VERSION,
            "installed_at": datetime.datetime.now().isoformat(),
            "system_install": self.system_install,
            "bin_dir": str(self.bin_dir),
            "app_dir": str(self.app_dir),
            "apps_dir": str(self.apps_dir),
            "icons_dir": str(self.icons_dir),
            "installed_files": self.installed_files,
            "installed_dirs": self.installed_dirs,
        }
        if not self.dry_run:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self._manifest_path(), "w") as fh:
                json.dump(manifest, fh, indent=2)

    def _load_manifest(self) -> Optional[dict]:
        mp = self._manifest_path()
        if not mp.exists():
            return None
        try:
            with open(mp) as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            return None

    # ── NVIDIA detection ──────────────────────────────────────────────────

    @staticmethod
    def _has_nvidia_gpu() -> bool:
        """Check if the system has an NVIDIA GPU."""
        try:
            result = subprocess.run(
                ["lspci"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, timeout=5,
            )
            return "nvidia" in result.stdout.lower()
        except (subprocess.SubprocessError, FileNotFoundError):
            # Try alternative detection
            return Path("/proc/driver/nvidia/version").exists()

    # ── dependency verification ───────────────────────────────────────────

    def verify_dependencies(self) -> bool:
        """Check for required, optional, and hardware-specific packages."""
        self._log("Checking system dependencies...")
        missing_critical: List[tuple] = []

        # Required packages
        for pkg_name, description, critical in REQUIRED_SYSTEM_PACKAGES:
            if self._is_package_installed(pkg_name):
                self._log(f"  ✓ {pkg_name}")
            else:
                self._log(f"  ✗ {pkg_name} — {description}")
                if critical:
                    missing_critical.append((pkg_name, description))

        # Optional packages (warn only)
        self._log("\nChecking optional packages...")
        for pkg_name, description in OPTIONAL_SYSTEM_PACKAGES:
            if self._is_package_installed(pkg_name):
                self._log(f"  ✓ {pkg_name}")
            else:
                self._log(f"  ⚠ {pkg_name} — {description} (optional, recommended)")
                self._add_error(f"Optional package '{pkg_name}' ({description}) not installed.")

        # NVIDIA packages (mandatory if GPU detected)
        has_nvidia = self._has_nvidia_gpu()
        if has_nvidia:
            self._log("\nNVIDIA GPU detected — checking required NVIDIA packages...")
            for pkg_name, description in NVIDIA_PACKAGES:
                if self._is_package_installed(pkg_name):
                    self._log(f"  ✓ {pkg_name}")
                else:
                    self._log(f"  ✗ {pkg_name} — {description}")
                    missing_critical.append((pkg_name, description))
        else:
            self._log("\nNo NVIDIA GPU detected — skipping NVIDIA package checks.")

        if not missing_critical:
            self._log("\nAll required dependencies satisfied.\n")
            return True

        # Offer to install missing critical packages
        self._log(f"\n{len(missing_critical)} critical package(s) missing:")
        for pkg_name, desc in missing_critical:
            self._log(f"  • {pkg_name} — {desc}")
        self._log("")

        if self._prompt_yes_no("Would you like the installer to install them now?"):
            pkg_names = [p[0] for p in missing_critical]
            return self._install_packages(pkg_names)
        else:
            self._log("Cannot continue without critical dependencies.", "error")
            return False

    @staticmethod
    def _is_package_installed(package: str) -> bool:
        """Check if a dpkg package is installed."""
        try:
            result = subprocess.run(
                ["dpkg", "-s", package],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _install_packages(self, packages: List[str]) -> bool:
        """Install packages via apt-get."""
        if self.dry_run:
            self._log(f"  [DRY-RUN] apt-get install {' '.join(packages)}")
            return True
        self._log(f"Installing: {', '.join(packages)}...")
        try:
            subprocess.run(
                ["sudo", "apt-get", "update", "-qq"],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120,
            )
            subprocess.run(
                ["sudo", "apt-get", "install", "-y", "-qq"] + packages,
                check=True, timeout=300,
            )
            self._log("Dependencies installed successfully.\n")
            return True
        except subprocess.CalledProcessError as e:
            self._add_error(f"Failed to install packages: {e}")
            return False
        except subprocess.TimeoutExpired:
            self._add_error("Package installation timed out.")
            return False

    # ── source file validation ────────────────────────────────────────────

    def validate_source_files(self) -> bool:
        """Verify that all required source files exist before starting."""
        self._log("Validating source files...")
        missing = []
        for exe in EXECUTABLES:
            path = self.installer_dir / exe
            if not path.exists():
                missing.append(str(path))
        icon_path = self.installer_dir / "icons" / "vega-icon.png"
        if not icon_path.exists():
            missing.append(str(icon_path))
        if missing:
            self._log("ERROR: The following required files are missing:", "error")
            for m in missing:
                self._log(f"  ✗ {m}", "error")
            self._log("\nPlease run the build script first to generate these files.", "error")
            return False
        self._log("All source files present.\n")
        return True

    # ── sudo / install type ───────────────────────────────────────────────

    def check_sudo_access(self) -> bool:
        """Check if the current user has sudo access (non-interactive)."""
        try:
            result = subprocess.run(
                ["sudo", "-n", "true"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def setup_installation_type(self):
        """Determine installation type based on sudo access and user choice."""
        has_sudo = self.check_sudo_access()
        if has_sudo:
            self.system_install = self._prompt_yes_no(
                "Sudo access available. Would you like to install Vega system-wide?"
            )
            if self.system_install:
                self._log("Proceeding with system-wide installation.\n")
            else:
                self._log("Proceeding with user-only installation.\n")
        else:
            self.system_install = False
            self._log("No sudo access detected. Proceeding with user-only installation.\n")

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

    # ── directory creation ────────────────────────────────────────────────

    def create_directories(self):
        """Create all necessary directories for the installation."""
        self._log("Creating installation directories...")
        use_sudo = self.system_install
        self._safe_makedirs(self.bin_dir, sudo=use_sudo)
        self._safe_makedirs(self.app_dir, sudo=use_sudo)
        self._safe_makedirs(self.apps_dir, sudo=use_sudo)
        self._safe_makedirs(self.icons_dir, sudo=use_sudo)
        self._safe_makedirs(self.autostart_dir)
        self._safe_makedirs(self.config_dir)
        self._log("")

    # ── executables ───────────────────────────────────────────────────────

    def install_executables(self):
        """Install the Vega executables to the appropriate directory."""
        self._log(f"Installing executables to {self.bin_dir}...")
        for exe in EXECUTABLES:
            src_path = self.installer_dir / exe
            dst_path = self.bin_dir / exe
            if self.dry_run:
                self._log(f"  [DRY-RUN] install {exe} → {dst_path}")
                self._record_file(dst_path)
                continue
            if self.system_install:
                ok = self._run_sudo_command(
                    ["install", "-m", "755", str(src_path), str(dst_path)],
                    description=f"install {exe}",
                )
                if ok:
                    self._record_file(dst_path)
            else:
                shutil.copy2(src_path, dst_path)
                os.chmod(
                    dst_path,
                    os.stat(dst_path).st_mode
                    | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
                )
                self._record_file(dst_path)
        self._log("")

    # ── icons ─────────────────────────────────────────────────────────────

    def install_icons(self):
        """Install the application icon and update the icon cache."""
        self._log("Installing icons...")
        src_icon = self.installer_dir / "icons" / "vega-icon.png"
        dst_icon = self.icons_dir / "vega-icon.png"

        if self.dry_run:
            self._log(f"  [DRY-RUN] install icon → {dst_icon}")
            self._record_file(dst_icon)
            self._log("")
            return

        if self.system_install:
            ok = self._run_sudo_command(
                ["install", "-m", "644", str(src_icon), str(dst_icon)],
                description="install icon",
            )
            if ok:
                self._record_file(dst_icon)
            self._run_sudo_command(
                ["gtk-update-icon-cache", "/usr/share/icons/hicolor/"],
                description="update icon cache",
            )
        else:
            shutil.copy2(src_icon, dst_icon)
            self._record_file(dst_icon)
            try:
                subprocess.run(
                    ["gtk-update-icon-cache", str(self.home / ".local/share/icons")],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
                )
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
        self._log("")

    # ── desktop entry ─────────────────────────────────────────────────────

    def create_desktop_entry(self):
        """Create and validate the desktop entry for Vega client."""
        self._log("Creating application menu entry...")
        desktop_content = f"""[Desktop Entry]
Type=Application
Name=Vega Client
Comment=Vega Client Application — Dynamic cooling, lighting, and clocking controller
Exec={self.bin_dir}/vega-client
Icon=vega-icon
Terminal=false
Categories=Utility;System;
"""
        apps_entry_path = self.apps_dir / "vega-client.desktop"

        if self.dry_run:
            self._log(f"  [DRY-RUN] create {apps_entry_path}")
            self._record_file(apps_entry_path)
            self._log("")
            return

        if self.system_install:
            ok = self._run_sudo_command(
                ["bash", "-c",
                 f"cat > {apps_entry_path} << 'EOT'\n{desktop_content}EOT\n"],
                description="create desktop entry",
            )
            if ok:
                self._record_file(apps_entry_path)
        else:
            with open(apps_entry_path, "w") as f:
                f.write(desktop_content)
            self._record_file(apps_entry_path)

        if self.desktop_dir.exists():
            desktop_entry_path = self.desktop_dir / "vega-client.desktop"
            with open(desktop_entry_path, "w") as f:
                f.write(desktop_content)
            os.chmod(desktop_entry_path,
                     os.stat(desktop_entry_path).st_mode | stat.S_IXUSR)
            self._record_file(desktop_entry_path)
        else:
            self._add_error(
                f"Desktop directory '{self.desktop_dir}' not found — "
                "skipping desktop shortcut."
            )
        self._validate_desktop_file(apps_entry_path)
        self._log("")

    def _validate_desktop_file(self, path: Path):
        """Run desktop-file-validate on a .desktop file (best-effort)."""
        try:
            result = subprocess.run(
                ["desktop-file-validate", str(path)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, timeout=5,
            )
            if result.returncode != 0:
                output = (result.stdout + result.stderr).strip()
                self._add_error(f"Desktop file validation warning: {output}")
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    # ── autostart services ────────────────────────────────────────────────

    def setup_autostart_services(self):
        """Configure gateway and user services to autostart on login."""
        self._log("Setting up autostart services...")
        services = {
            "vega-server-gateway": "Vega Server Gateway background service",
            "vega-server-user": "Vega Server User background service",
        }
        for svc_name, comment in services.items():
            content = f"""[Desktop Entry]
Type=Application
Exec=sh -c "{self.bin_dir}/{svc_name}"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name={svc_name.replace('-', ' ').title()}
Comment={comment}
"""
            entry_path = self.autostart_dir / f"{svc_name}.desktop"
            if self.dry_run:
                self._log(f"  [DRY-RUN] create {entry_path}")
            else:
                with open(entry_path, "w") as f:
                    f.write(content)
            self._record_file(entry_path)
        self._log("")

    # ── root service (systemd) ────────────────────────────────────────────

    def setup_root_service(self):
        """Set up the root service as a systemd service."""
        user_home = str(self.home)

        if self.system_install:
            self._log("Setting up root service as a systemd service...")
            service_content = f"""[Unit]
Description=Vega Server Root Service
After=network.target

[Service]
# VEGA_USER_HOME tells the root service where to store logs
# Without this, logs would go to /root/.config/vega_suit instead of
# the installing user's config directory
Environment="VEGA_USER_HOME={user_home}"
ExecStart={self.bin_dir}/vega-server-root
Restart=on-failure
User=root

[Install]
WantedBy=multi-user.target
"""
            service_file = Path("/etc/systemd/system/vega-server-root.service")

            if self.dry_run:
                self._log(f"  [DRY-RUN] create {service_file}")
                self._log("  [DRY-RUN] systemctl daemon-reload")
                self._log("  [DRY-RUN] systemctl enable vega-server-root.service")
                self._log("  [DRY-RUN] systemctl start vega-server-root.service")
            else:
                ok = self._run_sudo_command(
                    ["bash", "-c",
                     f"cat > {service_file} << 'EOT'\n{service_content}EOT\n"],
                    description="create systemd service file",
                )
                if ok:
                    self._record_file(service_file)
                self._run_sudo_command(
                    ["systemctl", "daemon-reload"], description="systemctl daemon-reload"
                )
                self._run_sudo_command(
                    ["systemctl", "enable", "vega-server-root.service"],
                    description="enable vega-server-root service",
                )
                self._run_sudo_command(
                    ["systemctl", "start", "vega-server-root.service"],
                    description="start vega-server-root service",
                )

            self._log("Root service installed and started as a systemd service.")
            self._log(f"Logs will be stored in {user_home}/.config/vega_suit/\n")
        else:
            self._log(
                "Note: Without system-wide installation, the root service "
                "cannot be set up as a systemd service."
            )
            self._log(f"The root service binary is at: {self.bin_dir}/vega-server-root")
            self._log("")
            self._log("To run manually with proper logging:")
            self._log(f'  VEGA_USER_HOME="{user_home}" sudo -E '
                       f"{self.bin_dir}/vega-server-root")
            self._log("")
            self._log("To install as a systemd service later, run:")
            self._log(f'  sudo cp "{self.bin_dir}/vega-server-root" /usr/local/bin/')
            manual_svc = (
                "  sudo bash -c 'cat > /etc/systemd/system/"
                "vega-server-root.service << EOT\n"
                "[Unit]\n"
                "Description=Vega Server Root Service\n"
                "After=network.target\n\n"
                "[Service]\n"
                f'Environment="VEGA_USER_HOME={user_home}"\n'
                "ExecStart=/usr/local/bin/vega-server-root\n"
                "Restart=on-failure\n"
                "User=root\n\n"
                "[Install]\n"
                "WantedBy=multi-user.target\n"
                "EOT'\n"
                "  sudo systemctl daemon-reload\n"
                "  sudo systemctl enable vega-server-root.service\n"
                "  sudo systemctl start vega-server-root.service"
            )
            self._log(manual_svc)
            self._log("")

    # ── $PATH management ──────────────────────────────────────────────────

    def setup_path(self):
        """Ensure the bin directory is on $PATH for user installs."""
        if self.system_install:
            return

        bin_str = str(self.bin_dir)
        current_path = os.environ.get("PATH", "")

        if bin_str in current_path.split(os.pathsep):
            self._log(f"'{bin_str}' is already on $PATH.\n")
            return

        profile_path = self.home / ".profile"
        if profile_path.exists():
            profile_text = profile_path.read_text()
            if bin_str in profile_text:
                self._log(f"'{bin_str}' is already configured in ~/.profile.\n")
                return

        self._log(f"'{bin_str}' is not on your $PATH.")
        if self._prompt_yes_no(
            "Add it to ~/.profile so Vega commands are available from the terminal?"
        ):
            if self.dry_run:
                self._log("  [DRY-RUN] would append to ~/.profile")
            else:
                export_line = (
                    f'\n# Added by Vega installer\n'
                    f'export PATH="$PATH:{bin_str}"\n'
                )
                with open(profile_path, "a") as f:
                    f.write(export_line)
            self._log(
                "Added to ~/.profile. Run 'source ~/.profile' or log out/in "
                "for the change to take effect.\n"
            )
        else:
            self._log(
                f"Skipped. You can manually add this to your shell profile:\n"
                f'  export PATH="$PATH:{bin_str}"\n'
            )

    # ── hardware / environment checks ─────────────────────────────────────

    def check_liquidctl_udev(self):
        """Check for liquidctl udev rules needed for non-root USB access."""
        self._log("Checking liquidctl udev rules...")
        udev_paths = [
            Path("/etc/udev/rules.d/71-liquidctl.rules"),
            Path("/lib/udev/rules.d/71-liquidctl.rules"),
            Path("/usr/lib/udev/rules.d/71-liquidctl.rules"),
        ]
        if any(p.exists() for p in udev_paths):
            self._log("  ✓ liquidctl udev rules found.\n")
            return

        self._log("  ✗ liquidctl udev rules not found.")
        self._log("    Without udev rules, non-root users cannot access USB watercooler devices.")

        if self._prompt_yes_no("Attempt to install liquidctl udev rules?"):
            # Try to locate rules from an installed liquidctl package
            rules_installed = False
            try:
                result = subprocess.run(
                    ["python3", "-c",
                     "import importlib.resources, liquidctl; "
                     "print(importlib.resources.files(liquidctl).joinpath('extra', '71-liquidctl.rules'))"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10,
                )
                if result.returncode == 0 and result.stdout.strip():
                    src_rules = Path(result.stdout.strip())
                    if src_rules.exists():
                        if not self.dry_run:
                            self._run_sudo_command(
                                ["cp", str(src_rules), "/etc/udev/rules.d/71-liquidctl.rules"],
                                description="install liquidctl udev rules",
                            )
                            self._run_sudo_command(
                                ["udevadm", "control", "--reload-rules"],
                                description="reload udev rules",
                            )
                            self._run_sudo_command(
                                ["udevadm", "trigger"],
                                description="trigger udev rules",
                            )
                        self._log("  ✓ liquidctl udev rules installed.")
                        rules_installed = True
            except (subprocess.SubprocessError, FileNotFoundError):
                pass

            if not rules_installed:
                self._log("  Could not auto-install. Please install manually:")
                self._log("    sudo cp /path/to/71-liquidctl.rules /etc/udev/rules.d/")
                self._log("    sudo udevadm control --reload-rules && sudo udevadm trigger")
                self._add_error("liquidctl udev rules not installed — USB device access may fail.")
        else:
            self._add_error("liquidctl udev rules not installed — USB device access may fail for non-root users.")
        self._log("")

    def check_i2c_dev_module(self):
        """Check if i2c-dev kernel module is loaded (needed by OpenRGB for SMBus)."""
        self._log("Checking i2c-dev kernel module...")
        if Path("/sys/module/i2c_dev").exists():
            self._log("  ✓ i2c-dev module is loaded.\n")
            return

        self._log("  ✗ i2c-dev module is not loaded.")
        self._log("    OpenRGB needs this module to access RAM/motherboard RGB via SMBus.")

        if self._prompt_yes_no("Load i2c-dev now and persist across reboots?"):
            if self.dry_run:
                self._log("  [DRY-RUN] modprobe i2c-dev")
                self._log("  [DRY-RUN] echo 'i2c-dev' >> /etc/modules-load.d/i2c-dev.conf")
            else:
                self._run_sudo_command(
                    ["modprobe", "i2c-dev"], description="load i2c-dev module"
                )
                self._run_sudo_command(
                    ["bash", "-c", "echo 'i2c-dev' > /etc/modules-load.d/i2c-dev.conf"],
                    description="persist i2c-dev module",
                )
            self._log("  ✓ i2c-dev module loaded and persisted.\n")
        else:
            self._add_error("i2c-dev module not loaded — OpenRGB SMBus access may not work.")
            self._log("")

    def check_openrgb_status(self):
        """Check if OpenRGB is installed and provide setup guidance."""
        self._log("Checking OpenRGB SDK server...")

        # Check if openrgb binary is available
        openrgb_found = shutil.which("openrgb") is not None
        if not openrgb_found:
            # Check flatpak
            try:
                result = subprocess.run(
                    ["flatpak", "list", "--app"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, timeout=10,
                )
                if result.returncode == 0 and "openrgb" in result.stdout.lower():
                    openrgb_found = True
            except (subprocess.SubprocessError, FileNotFoundError):
                pass

        if openrgb_found:
            self._log("  ✓ OpenRGB is installed.")
        else:
            self._log("  ✗ OpenRGB is not installed.")

        self._log("")
        self._log("  ╔══════════════════════════════════════════════════════════════╗")
        self._log("  ║  IMPORTANT: Vega's lighting system requires OpenRGB SDK     ║")
        self._log("  ║  server to be running on localhost:6742.                    ║")
        self._log("  ║                                                              ║")
        self._log("  ║  To set up:                                                  ║")
        self._log("  ║  1. Install OpenRGB from https://openrgb.org/               ║")
        self._log("  ║  2. Open OpenRGB → SDK Server → Start Server                ║")
        self._log("  ║  3. Or run: openrgb --server                                ║")
        self._log("  ║  4. Optionally enable autostart for the SDK server           ║")
        self._log("  ╚══════════════════════════════════════════════════════════════╝")
        self._log("")

    def check_lm_sensors(self):
        """Check if hardware sensors are available for CPU temperature monitoring."""
        self._log("Checking hardware sensor availability...")
        hwmon_path = Path("/sys/class/hwmon")
        if hwmon_path.exists() and any(hwmon_path.iterdir()):
            self._log("  ✓ Hardware sensors detected in /sys/class/hwmon/\n")
        else:
            self._log("  ⚠ No hardware sensors found in /sys/class/hwmon/")
            self._log("    CPU temperature monitoring may not work.")
            self._log("    Try running: sudo sensors-detect")
            self._add_error("No hardware sensors detected — CPU temperature monitoring may fail.")
            self._log("")

    # ── post-install health check ─────────────────────────────────────────

    def verify_installation(self):
        """Verify that the installation completed successfully."""
        self._log("Running post-install health check...")
        all_ok = True

        # Check executables exist and are executable
        for exe in EXECUTABLES:
            exe_path = self.bin_dir / exe
            if self.dry_run:
                self._log(f"  [DRY-RUN] would verify {exe_path}")
                continue
            if exe_path.exists() and os.access(str(exe_path), os.X_OK):
                self._log(f"  ✓ {exe} is installed and executable")
            else:
                self._log(f"  ✗ {exe} — missing or not executable at {exe_path}")
                self._add_error(f"Executable {exe} not found or not executable at {exe_path}")
                all_ok = False

        # Check desktop entry
        desktop_entry = self.apps_dir / "vega-client.desktop"
        if self.dry_run:
            pass
        elif desktop_entry.exists():
            self._log(f"  ✓ Desktop entry exists")
        else:
            self._log(f"  ✗ Desktop entry missing at {desktop_entry}")
            all_ok = False

        # Check autostart entries
        for svc in ["vega-server-gateway", "vega-server-user"]:
            autostart_file = self.autostart_dir / f"{svc}.desktop"
            if self.dry_run:
                pass
            elif autostart_file.exists():
                self._log(f"  ✓ {svc} autostart configured")
            else:
                self._log(f"  ✗ {svc} autostart entry missing")
                all_ok = False

        # Check systemd service (system install only)
        if self.system_install and not self.dry_run:
            try:
                result = subprocess.run(
                    ["systemctl", "is-active", "vega-server-root.service"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, timeout=5,
                )
                if result.stdout.strip() == "active":
                    self._log("  ✓ vega-server-root systemd service is active")
                else:
                    self._log(f"  ⚠ vega-server-root service is {result.stdout.strip()}")
                    self._add_error(
                        f"vega-server-root service is {result.stdout.strip()} "
                        "(expected 'active')"
                    )
                    all_ok = False
            except (subprocess.SubprocessError, FileNotFoundError):
                self._add_error("Could not check vega-server-root service status.")
                all_ok = False

        if all_ok:
            self._log("\n  ✓ All health checks passed.\n")
        else:
            self._log("\n  ⚠ Some health checks failed — see warnings above.\n")

    # ── rollback ──────────────────────────────────────────────────────────

    def rollback(self):
        """Remove all files and directories created during this installation."""
        self._log("\nRolling back installation...")
        for f in reversed(self.installed_files):
            fp = Path(f)
            if fp.exists():
                try:
                    if self.system_install and not os.access(str(fp), os.W_OK):
                        self._run_sudo_command(
                            ["rm", "-f", str(fp)], description=f"rollback remove {fp.name}"
                        )
                    else:
                        fp.unlink()
                    self._log(f"  Removed: {fp}")
                except OSError as e:
                    self._log(f"  Failed to remove {fp}: {e}", "error")

        for d in reversed(self.installed_dirs):
            dp = Path(d)
            if dp.exists() and not any(dp.iterdir()):
                try:
                    if self.system_install and not os.access(str(dp), os.W_OK):
                        self._run_sudo_command(
                            ["rmdir", str(dp)], description=f"rollback remove dir {dp.name}"
                        )
                    else:
                        dp.rmdir()
                    self._log(f"  Removed dir: {dp}")
                except OSError:
                    pass
        self._log("Rollback complete.")

    # ── uninstall ─────────────────────────────────────────────────────────

    def run_uninstall(self):
        """Cleanly uninstall Vega using the saved manifest."""
        self._log("Vega Application Uninstaller")
        self._log("============================\n")

        manifest = self._load_manifest()
        if manifest is None:
            self._log(
                f"No installation manifest found at:\n  {self._manifest_path()}\n\n"
                "Cannot determine what was installed. You may need to remove files manually.",
                "error",
            )
            return 1

        is_system = manifest.get("system_install", False)
        files = manifest.get("installed_files", [])
        dirs = manifest.get("installed_dirs", [])
        bin_dir = manifest.get("bin_dir", "")
        installed_at = manifest.get("installed_at", "unknown")

        self._log(f"Found manifest (version {manifest.get('version', '?')}).")
        self._log(f"Installed at: {installed_at}")
        self._log(f"Installation type: {'system-wide' if is_system else 'user-only'}")
        self._log(f"Files to remove: {len(files)}")
        self._log(f"Directories to remove: {len(dirs)}\n")

        if not self._prompt_yes_no("Proceed with uninstallation?"):
            self._log("Uninstall canceled.")
            return 0

        if is_system:
            self._log("Stopping and disabling systemd service...")
            self._run_sudo_command(
                ["systemctl", "stop", "vega-server-root.service"],
                description="stop root service",
            )
            self._run_sudo_command(
                ["systemctl", "disable", "vega-server-root.service"],
                description="disable root service",
            )
            self._run_sudo_command(["systemctl", "daemon-reload"], description="daemon-reload")

        self._log("Removing installed files...")
        for f in files:
            fp = Path(f)
            if fp.exists():
                try:
                    if is_system and not os.access(str(fp), os.W_OK):
                        self._run_sudo_command(
                            ["rm", "-f", str(fp)], description=f"remove {fp.name}"
                        )
                    else:
                        fp.unlink()
                    self._log(f"  Removed: {fp}")
                except OSError as e:
                    self._add_error(f"Failed to remove {fp}: {e}")

        self._log("Removing empty directories...")
        for d in reversed(dirs):
            dp = Path(d)
            if dp.exists():
                try:
                    if not any(dp.iterdir()):
                        if is_system and not os.access(str(dp), os.W_OK):
                            self._run_sudo_command(
                                ["rmdir", str(dp)], description=f"remove dir {dp.name}"
                            )
                        else:
                            dp.rmdir()
                        self._log(f"  Removed: {dp}")
                except OSError:
                    pass

        if bin_dir and not is_system:
            self._clean_profile_path(bin_dir)

        manifest_path = self._manifest_path()
        if manifest_path.exists():
            manifest_path.unlink()
            self._log(f"  Removed manifest: {manifest_path}")

        if is_system:
            self._run_sudo_command(
                ["gtk-update-icon-cache", "/usr/share/icons/hicolor/"],
                description="update icon cache",
            )

        self._log("")
        self._print_error_summary()
        self._log("Uninstallation complete.")
        return 0

    def _clean_profile_path(self, bin_dir: str):
        """Remove the PATH export line we added to ~/.profile."""
        profile_path = self.home / ".profile"
        if not profile_path.exists():
            return
        try:
            lines = profile_path.read_text().splitlines(keepends=True)
            marker = "# Added by Vega installer"
            export_fragment = f'export PATH="$PATH:{bin_dir}"'
            new_lines = []
            skip_next = False
            for line in lines:
                if skip_next:
                    skip_next = False
                    if export_fragment in line:
                        continue
                    else:
                        new_lines.append(line)
                        continue
                if marker in line:
                    skip_next = True
                    continue
                new_lines.append(line)
            profile_path.write_text("".join(new_lines))
            self._log("  Cleaned PATH entry from ~/.profile")
        except OSError:
            pass

    # ── existing install detection ────────────────────────────────────────

    def check_existing_installation(self) -> bool:
        """Check for an existing installation and prompt the user.

        Returns:
            True if installation should proceed, False to abort.
        """
        manifest = self._load_manifest()
        if manifest is None:
            return True  # No existing install, proceed

        installed_at = manifest.get("installed_at", "unknown")
        version = manifest.get("version", "unknown")
        install_type = "system-wide" if manifest.get("system_install") else "user-only"

        self._log("An existing Vega installation was detected:")
        self._log(f"  Version:  {version}")
        self._log(f"  Date:     {installed_at}")
        self._log(f"  Type:     {install_type}\n")

        if self._prompt_yes_no("Would you like to overwrite this installation?"):
            self._log("Proceeding with reinstallation.\n")
            return True
        else:
            self._log("Installation canceled.")
            return False

    # ── main install flow ─────────────────────────────────────────────────

    def run_installation(self):
        """Run the complete installation process with tracking and rollback."""
        self._log("Vega Application Installer")
        self._log("==========================")
        self._log(f"Version {VERSION}")
        if self.dry_run:
            self._log("*** DRY-RUN MODE — no changes will be made ***")
        self._log("")

        # Step 0: Existing installation check
        if not self.check_existing_installation():
            return 0

        # Step 1: Verify dependencies
        if not self.verify_dependencies():
            return 1

        # Step 2: Validate source files
        if not self.validate_source_files():
            return 1

        # Step 3: Choose installation type
        self.setup_installation_type()

        # Step 4: Hardware and environment checks
        self.check_lm_sensors()
        self.check_liquidctl_udev()
        self.check_i2c_dev_module()
        self.check_openrgb_status()

        # Step 5: Install everything (with rollback on critical failure)
        try:
            self.create_directories()
            self.install_executables()
            self.install_icons()
            self.create_desktop_entry()
            self.setup_autostart_services()
            self.setup_root_service()
            self.setup_path()
        except Exception as e:
            self._log(f"\nCritical error during installation: {e}", "error")
            self.rollback()
            return 1

        # Step 6: Save manifest
        self._save_manifest()

        # Step 7: Post-install health check
        self.verify_installation()

        # Step 8: Print summary
        self._log("=" * 50)
        self._log("Installation complete!")
        self._log("=" * 50)
        self._log(
            "You can find Vega Client in your applications menu"
            + (" and on your desktop." if self.desktop_dir.exists() else ".")
        )
        self._log("Background services have been configured to start automatically at login.")
        self._log(f"Logs will be stored in {self.home}/.config/vega_suit/")
        self._log(f"Install log: {self.config_dir / 'install.log'}")
        self._log("")

        self._print_error_summary()
        return 0

    # ── error summary ─────────────────────────────────────────────────────

    def _print_error_summary(self):
        """Print accumulated non-fatal errors, if any."""
        if not self.errors:
            return
        self._log(f"⚠ {len(self.errors)} warning(s) occurred during the process:")
        for i, err in enumerate(self.errors, 1):
            self._log(f"  {i}. {err}")
        self._log("")

    # ── utility ───────────────────────────────────────────────────────────

    @staticmethod
    def _prompt_yes_no(question: str) -> bool:
        """Prompt the user for a yes/no answer."""
        print(f"{question} (y/n)")
        while True:
            choice = input().strip().lower()
            if choice in ("y", "yes"):
                return True
            elif choice in ("n", "no"):
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the installer."""
    parser = argparse.ArgumentParser(
        prog="vega-installer",
        description="Vega Application Installer — installs and configures the "
                    "Vega dynamic cooling, lighting, and clocking controller suite.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python installer.py               Install Vega (interactive)\n"
            "  python installer.py --uninstall    Remove a previous installation\n"
            "  python installer.py --dry-run      Preview installation steps\n"
            "  python installer.py --version      Show version\n"
        ),
    )
    parser.add_argument(
        "--uninstall", action="store_true",
        help="Uninstall a previous Vega installation using the saved manifest.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what the installer would do without making changes.",
    )
    parser.add_argument(
        "--log", metavar="PATH", default=None,
        help="Path to the install log file (default: ~/.config/vega_suit/install.log).",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {VERSION}",
    )
    return parser


def main() -> int:
    """Main entry point for the Vega installer."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        installer = VegaInstaller(dry_run=args.dry_run, log_path=args.log)

        if args.uninstall:
            return installer.run_uninstall()
        else:
            return installer.run_installation()

    except KeyboardInterrupt:
        print("\nOperation canceled by user.")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
