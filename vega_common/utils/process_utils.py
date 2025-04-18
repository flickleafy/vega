\
"""
Process utilities for the Vega project.

This module provides functions for listing and filtering system processes.
"""
import psutil
from typing import Set, List

# TODO: Consider making these lists configurable or loading from a file
ignore_list = ['cryptd', 'btrfs', 'kworker', 'kthreadd',
               'systemd', 'mount', 'napi', 'sleep', 'rcu',
               'nvidia', 'slub', 'netns', 'migration',
               'idle', 'sudo', 'cpu', 'irq', 'vfio', 'acpi',
               'zswap', 'ipv6', 'nvme', 'charger', 'watchdog',
               'postgres', 'docker', 'kernel', 'container',
               'libvirt', 'preload', 'session', 'gdm', 'python',
               'daemon', 'queue', 'bluetooth', 'scsi', 'raid',
               'mongo', 'node', 'registry', 'gvfsd', 'gnome',
               'shell', 'identity', 'redis', 'pipewire', 'dnsmasq',
               'iprt', 'cron', 'snapd', 'php', 'xorg', 'pihole',
               'master', 'notify', 'nacl', 'ksmd', 'tracker',
               'modem', 'network', 'agent', 'bash', 'integrity',
               'pulse', 'java', 'crash', 'ibus', 'dbus', 'snyk',
               'dconf', 'gsd', 'qmgr', 'clam', 'volume', 'monitor',
               'tray', 'power', 'compact', 'sys', 'color', 'notifier',
               'xdg', 'store', 'disk', 'crypt', 'control', 'uvm',
               'server', 'factory', 'audit', 'kdev', 'swap', 'ata',
               'launcher', 'glib', 'package', 'cfg', 'dhcp', 'http',
               'inet', 'wpa', 'block', 'poller']

strict_ignore_list = ['md', 'mld', 'sh', 'gjs', 'cat', 'tor']

# --- Application Lists for Power Plan Detection ---
BALANCE_APP_LIST = [
    'vdf.gui',         # Video Comparer
    'dupeguru',        # File duplicate finder
    'celluloid',       # Media player
    'mpv',             # Media player
    'firefox',         # Web Browser
    'chrome',          # Web Browser
    'chromium',        # Web Browser
    'brave',           # Web Browser
    'opera',           # Web Browser
    'vivaldi',         # Web Browser
    'thunderbird',     # Email Client
    'evolution',       # Email/Groupware Client
    'soffice.bin',     # LibreOffice main process
    'lowriter',        # LibreOffice Writer
    'localc',          # LibreOffice Calc
    'loimpress',       # LibreOffice Impress
    'vlc',             # Media Player
    'rhythmbox',       # Music Player
    'spotify',         # Music Streaming
    'slack',           # Communication
    'discord',         # Communication
    'telegram-desktop',# Communication
    'nautilus',        # File Manager (GNOME)
    'dolphin',         # File Manager (KDE)
    'thunar',          # File Manager (XFCE)
    'transmission-gtk',# Torrent Client
    'qbittorrent',     # Torrent Client
    'deluge',          # Torrent Client
    'evince',          # Document Viewer (GNOME)
    'okular',          # Document Viewer (KDE)
    'zathura',         # Document Viewer
    'eog',             # Image Viewer (Eye of GNOME)
    'gwenview',        # Image Viewer (KDE)
    'shotwell',        # Photo Manager
    'darktable',       # Photo Workflow (can be intensive, but often manageable on balanced)
    'rawtherapee',     # Photo Workflow (similar to darktable)
    'audacity',        # Audio Editor (can be intensive, but often manageable)
    'calibre',         # E-book Management
    'keepassxc',       # Password Manager
    'signal-desktop',  # Secure Messenger
    # Add other common desktop applications as needed
]
PERFORMANCE_APP_LIST = [
    'vmware',          # Virtualization
    'virtualbox',      # Virtualization
    'qemu',            # Virtualization/Emulation
    'steam',           # Gaming Platform
    'lutris',          # Gaming Platform
    'heroic',          # Gaming Platform
    'zoom',            # Video Conferencing
    'teams',           # Video Conferencing (Microsoft Teams)
    'blender',         # 3D Modeling/Rendering
    'kdenlive',        # Video Editing
    'openshot',        # Video Editing
    'resolve',         # Video Editing (DaVinci Resolve)
    'premiere',        # Video Editing (Adobe Premiere - if running via Wine/Proton)
    'gimp',            # Image Editing
    'krita',           # Image Editing
    'photoshop',       # Image Editing (Adobe Photoshop - if running via Wine/Proton)
    'code',            # Development IDE (VS Code)
    'pycharm',         # Development IDE
    'idea',            # Development IDE (IntelliJ)
    'android-studio',  # Development IDE
    'obs',             # Streaming/Recording (OBS Studio)
    'ardour',          # Digital Audio Workstation (Real-time audio)
    'reaper',          # Digital Audio Workstation (Real-time audio - often via Wine)
    'bitwig-studio',   # Digital Audio Workstation (Real-time audio)
    'jackd',           # Real-time Audio Server
    'carla',           # Audio Plugin Host (Real-time audio)
    # Add specific game executable names if needed, e.g., 'csgo_linux64'
    # Add scientific computing/simulation software if relevant, e.g., 'matlab'
]


def similar_string_list(string: str, ignore: List[str], strict_ignore: List[str]) -> bool:
    """
    Check if a string contains any substring from the ignore lists.

    Args:
        string (str): The string to check.
        ignore (List[str]): List of substrings to check for containment.
        strict_ignore (List[str]): List of exact strings to check for equality.

    Returns:
        bool: True if the string matches any ignore criteria, False otherwise.
    """
    # O(S * L) where S is the length of the string and L is the number of items in ignore list
    # Can be optimized using Aho-Corasick or similar if performance is critical
    for item in ignore:
        if item in string:
            return True
    # O(T) where T is the number of items in strict_ignore list
    for item in strict_ignore:
        if item == string:
            return True
    return False


def get_process_list() -> Set[str]:
    """
    Get a filtered list of running process names.

    Retrieves all running process names, converts them to lowercase,
    and filters out common system/background processes based on predefined lists.

    Returns:
        Set[str]: A set of filtered process names.
        
    Raises:
        psutil.Error: If there's an issue iterating through processes.
    """
    process_set: Set[str] = set()
    # O(P) where P is the number of processes
    for process in psutil.process_iter(['name']): # Request only name for efficiency
        try:
            # Get process name
            process_name = process.info['name'].lower()
            process_set.add(process_name)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # Ignore processes that ended, are restricted, or are zombies
            pass
        except psutil.Error as e:
            print(f"Error accessing process info: {e}")
            # Decide whether to raise or continue based on requirements
            # For now, continue to get as many processes as possible
            continue

    filtered_process_set: Set[str] = set()
    # O(N * (S*L + T)) where N is the number of unique process names
    for process_name in process_set:
        if not similar_string_list(process_name, ignore_list, strict_ignore_list):
            filtered_process_set.add(process_name)

    return filtered_process_set


# --- Application Detection Functions ---
# Moved from cpuclocking/detectBalance.py
def detect_balance_apps(process_list: Set[str]) -> bool:
    """Check if any 'balance' profile applications are running.

    Args:
        process_list (Set[str]): A set of running process names (lowercase).

    Returns:
        bool: True if a balance-triggering app is found, False otherwise.
        
    Complexity: O(B * P) where B is the number of balance apps and P is the average length of process names (string search).
                Can be O(B) if process_list is a hash set and we do exact matches.
    """
    # O(B) iteration, assuming set lookup is O(1) on average
    for app in BALANCE_APP_LIST:
        # Check for exact match first (more efficient if applicable)
        if app in process_list:
             return True
        # Optional: Check for substring match if needed (more expensive)
        # for process_name in process_list:
        #     if app in process_name:
        #         return True
    return False


# Moved from cpuclocking/detectPerformance.py
def detect_performance_apps(process_list: Set[str]) -> bool:
    """Check if any 'performance' profile applications are running.

    Args:
        process_list (Set[str]): A set of running process names (lowercase).

    Returns:
        bool: True if a performance-triggering app is found, False otherwise.
        
    Complexity: O(P * Q) where P is the number of performance apps and Q is the average length of process names (string search).
                Can be O(P) if process_list is a hash set and we do exact matches.
    """
    # O(P) iteration, assuming set lookup is O(1) on average
    for app in PERFORMANCE_APP_LIST:
        # Check for exact match first
        if app in process_list:
            return True
        # Optional: Check for substring match if needed
        # for process_name in process_list:
        #     if app in process_name:
        #         return True
    return False

