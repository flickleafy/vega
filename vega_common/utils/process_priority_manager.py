"""
Process priority management for thermal control.

This module provides a decoupled system for managing process priorities
independently of the CPU power plan mechanism. It supports multi-layer
priority levels, spike detection, and suggestion storage for background apps.
"""

import json
import os
import psutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from vega_common.utils.logging_utils import get_module_logger

logger = get_module_logger("vega_common/utils/process_priority_manager")


class PriorityLevel(IntEnum):
    """Priority levels with corresponding nice values.
    
    Each level represents a graduated decrease in process priority,
    allowing fine-grained control over thermal management response.
    """
    NORMAL = 0       # nice 0 - default priority
    REDUCED = 1      # nice 5 - slightly reduced
    LOW = 2          # nice 10 - low priority
    BACKGROUND = 3   # nice 19 - lowest priority (fully backgrounded)


# Mapping from priority levels to Linux nice values
NICE_VALUES: Dict[PriorityLevel, int] = {
    PriorityLevel.NORMAL: 0,
    PriorityLevel.REDUCED: 5,
    PriorityLevel.LOW: 10,
    PriorityLevel.BACKGROUND: 19,
}

# Mapping from priority levels to I/O priority classes
# Note: IOPRIO_CLASS_IDLE means process only gets I/O when disk is idle
IONICE_CLASSES: Dict[PriorityLevel, int] = {
    PriorityLevel.NORMAL: psutil.IOPRIO_CLASS_NONE,
    PriorityLevel.REDUCED: psutil.IOPRIO_CLASS_BE,  # Best effort, default
    PriorityLevel.LOW: psutil.IOPRIO_CLASS_BE,       # Best effort with lower priority
    PriorityLevel.BACKGROUND: psutil.IOPRIO_CLASS_IDLE,  # Only when idle
}


# === Application Lists ===

# Apps that are safe to deprioritize - these can wait without user noticing
SAFE_LOW_PRIORITY_APPS: Set[str] = {
    # File operations (CPU-intensive but can wait)
    "dupeguru",           # Duplicate finder
    "vdf.gui",            # Video comparer
    "rsync",              # File sync
    "rclone",             # Cloud sync
    "baobab",             # Disk analyzer (GNOME)
    "filelight",          # Disk analyzer (KDE)
    "qdirstat",           # Disk usage analyzer
    "ncdu",               # NCurses disk usage
    
    # Indexing/Background tasks
    "tracker-miner-fs",   # GNOME file indexer
    "tracker-miner-fs-3", # GNOME file indexer v3
    "baloo_file",         # KDE file indexer
    "baloo_file_extractor", # KDE file indexer extractor
    "updatedb",           # locate database update
    "mlocate",            # Modern locate
    "plocate",            # Faster plocate
    
    # Compression/Conversion (can run slower)
    "7z",                 # 7-Zip compression
    "7za",                # 7-Zip standalone
    "gzip",               # Gzip compression
    "pigz",               # Parallel gzip
    "bzip2",              # Bzip2 compression
    "pbzip2",             # Parallel bzip2
    "xz",                 # XZ compression
    "pixz",               # Parallel xz
    "zstd",               # Zstandard compression
    "lz4",                # Fast compression
    "unrar",              # RAR extraction
    "unzip",              # ZIP extraction
    "tar",                # Archive tool
    
    # Media encoding (CPU-intensive background tasks)
    "ffmpeg",             # Media conversion (non-interactive)
    "ffprobe",            # Media analysis
    "handbrake",          # Video encoding
    "HandBrakeCLI",       # HandBrake CLI
    "x264",               # H.264 encoder
    "x265",               # H.265/HEVC encoder
    "av1an",              # AV1 encoder wrapper
    "rav1e",              # Rust AV1 encoder
    "svt-av1",            # SVT-AV1 encoder
    
    # Downloads/Transfers (I/O and network bound)
    "transmission-gtk",   # Torrent client
    "transmission-daemon", # Torrent daemon
    "qbittorrent",        # Torrent client
    "deluge",             # Torrent client
    "aria2c",             # Download manager
    "wget",               # Downloads
    "curl",               # Transfers
    
    # Backups (can run slower without user impact)
    "restic",             # Backup
    "borgbackup",         # Backup
    "borg",               # Borg backup
    "timeshift",          # System backup
    "deja-dup",           # GNOME backup
    "duplicity",          # Backup
    "rsyncd",             # Rsync daemon
    
    # Build tools (can use lower priority)
    "make",               # Build system
    "ninja",              # Build system
    "cargo",              # Rust build
    "rustc",              # Rust compiler
    "gcc",                # GCC compiler
    "g++",                # G++ compiler
    "clang",              # Clang compiler
    "clang++",            # Clang++ compiler
    "ld",                 # Linker
    
    # Package management/updates
    "apt",                # APT
    "apt-get",            # APT
    "dpkg",               # Debian packages
    "dnf",                # Fedora packages
    "yum",                # Old Fedora packages
    "pacman",             # Arch packages
    "flatpak",            # Flatpak
    "snap",               # Snap packages
}

# NEVER reduce priority of these (system-critical processes)
PROTECTED_APPS: Set[str] = {
    # Init and core system
    "systemd", "init", "kernel", "kthread",
    
    # Session management
    "dbus-daemon", "dbus-broker", 
    "polkitd", "polkit",
    
    # Display/Graphics
    "xorg", "Xorg", "X",
    "wayland", "weston",
    "gnome-shell", "plasmashell", "kwin", "mutter",
    "sddm", "gdm", "lightdm", "ly",
    
    # Audio (real-time requirements)
    "pulseaudio", "pipewire", "pipewire-pulse",
    "wireplumber", "jackd", "jackdbus",
    
    # Networking
    "networkmanager", "NetworkManager",
    "systemd-resolved", "systemd-networkd",
    "dhclient", "dhcpcd",
    
    # Security
    "sshd", "gpg-agent", "gnome-keyring-daemon",
    
    # User session
    "login", "su", "sudo",
    "systemd-logind", "elogind",
}


@dataclass
class ProcessPriorityState:
    """Tracks priority changes made to a process for later restoration.
    
    Attributes:
        pid: Process ID
        name: Process name (lowercase)
        original_nice: Original nice value before modification
        original_ionice: Original I/O priority class
        current_level: Current PriorityLevel applied
        changed_at: Timestamp when priority was changed
    """
    pid: int
    name: str
    original_nice: int
    original_ionice: Optional[int] = None
    current_level: PriorityLevel = PriorityLevel.NORMAL
    changed_at: datetime = field(default_factory=datetime.now)


class ProcessPriorityManager:
    """Manages process priorities independently of CPU power plans.
    
    This class provides multi-layer priority control for background processes
    to help manage thermal pressure. It operates completely independently of
    the CPU governor/power plan mechanism.
    
    Features:
        - Multi-layer priority levels (normal → reduced → low → background)
        - Protected apps list to prevent harming system stability
        - Spike detection to identify high-CPU processes
        - Suggestion storage for user review
        - State tracking for priority restoration
    
    Example:
        >>> manager = ProcessPriorityManager()
        >>> manager.lower_priority(level=PriorityLevel.LOW)
        >>> # Later, when thermal pressure is resolved:
        >>> manager.restore_priorities()
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize the process priority manager.
        
        Args:
            config_dir: Directory for config/suggestion files.
                        Defaults to ~/.config/vega_suit/vega_common/priority_manager
        """
        self.config_dir = config_dir or Path.home() / ".config" / "vega_suit" / "vega_common" / "priority_manager"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.suggestions_file = self.config_dir / "suggested_low_priority_apps.json"
        self.config_file = self.config_dir / "priority_config.json"
        
        # Track modified processes for restoration
        self._modified_processes: Dict[int, ProcessPriorityState] = {}
        
        # Load user-configured low priority apps
        self.custom_low_priority_apps: Set[str] = self._load_custom_apps()
        
        logger.info(
            f"ProcessPriorityManager initialized. Config dir: {self.config_dir}. "
            f"Tracking {len(SAFE_LOW_PRIORITY_APPS)} safe apps + "
            f"{len(self.custom_low_priority_apps)} custom apps."
        )
    
    def _load_custom_apps(self) -> Set[str]:
        """Load user-configured low priority apps from config file."""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    data = json.load(f)
                    apps = set(data.get("low_priority_apps", []))
                    logger.debug(f"Loaded {len(apps)} custom low priority apps from config")
                    return apps
            except json.JSONDecodeError as e:
                logger.warning(f"Could not parse priority config: {e}")
            except Exception as e:
                logger.warning(f"Could not load priority config: {e}")
        return set()
    
    def _save_config(self) -> None:
        """Save current configuration to file."""
        try:
            data = {
                "low_priority_apps": list(self.custom_low_priority_apps),
                "updated_at": datetime.now().isoformat(),
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved priority config to {self.config_file}")
        except Exception as e:
            logger.warning(f"Could not save priority config: {e}")
    
    def get_low_priority_apps(self) -> Set[str]:
        """Get combined set of safe + custom low priority apps.
        
        Returns:
            Set of app names that should be deprioritized under thermal pressure.
        """
        return SAFE_LOW_PRIORITY_APPS | self.custom_low_priority_apps
    
    def add_custom_app(self, app_name: str) -> None:
        """Add an app to the custom low priority list.
        
        Args:
            app_name: App name to add (case-sensitive).
        """
        self.custom_low_priority_apps.add(app_name.lower())
        self._save_config()
        logger.info(f"Added '{app_name}' to custom low priority apps")
    
    def remove_custom_app(self, app_name: str) -> bool:
        """Remove an app from the custom low priority list.
        
        Args:
            app_name: App name to remove.
            
        Returns:
            True if removed, False if not found.
        """
        try:
            self.custom_low_priority_apps.remove(app_name.lower())
            self._save_config()
            logger.info(f"Removed '{app_name}' from custom low priority apps")
            return True
        except KeyError:
            return False
    
    def is_protected(self, process_name: str) -> bool:
        """Check if a process is protected from priority changes.
        
        Args:
            process_name: Process name to check.
            
        Returns:
            True if process should never have priority lowered.
        """
        name_lower = process_name.lower()
        return any(p in name_lower for p in PROTECTED_APPS)
    
    def lower_priority(
        self,
        app_names: Optional[Set[str]] = None,
        level: PriorityLevel = PriorityLevel.LOW,
        include_ionice: bool = True,
    ) -> Dict[str, bool]:
        """Lower priority of matching processes.
        
        Args:
            app_names: Specific apps to target. If None, uses configured list.
            level: Target priority level (REDUCED, LOW, or BACKGROUND).
            include_ionice: Also set I/O priority if True.
            
        Returns:
            Dict mapping "name:pid" to success status.
        
        Raises:
            ValueError: If level is NORMAL (use restore_priorities instead).
        """
        if level == PriorityLevel.NORMAL:
            raise ValueError("Use restore_priorities() to reset to normal priority")
        
        targets = app_names or self.get_low_priority_apps()
        nice_value = NICE_VALUES[level]
        ionice_class = IONICE_CLASSES[level]
        results: Dict[str, bool] = {}
        
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                name = proc.info['name'].lower()
                pid = proc.info['pid']
                key = f"{name}:{pid}"
                
                # Skip protected processes
                if self.is_protected(name):
                    continue
                
                # Check if this process should be targeted
                if name not in targets:
                    continue
                
                # Get current priority
                try:
                    original_nice = proc.nice()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                
                # Only lower if not already at or below target
                if original_nice >= nice_value:
                    results[key] = True  # Already at target or lower
                    continue
                
                # Store original state for restoration
                original_ionice = None
                if include_ionice and hasattr(proc, 'ionice'):
                    try:
                        ionice_info = proc.ionice()
                        original_ionice = ionice_info.ioclass
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Apply new priority
                try:
                    proc.nice(nice_value)
                    
                    if include_ionice and hasattr(proc, 'ionice'):
                        try:
                            proc.ionice(ionice_class)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass  # ionice is optional
                    
                    # Track the change
                    self._modified_processes[pid] = ProcessPriorityState(
                        pid=pid,
                        name=name,
                        original_nice=original_nice,
                        original_ionice=original_ionice,
                        current_level=level
                    )
                    
                    results[key] = True
                    logger.info(
                        f"Lowered priority of {name} (PID {pid}): "
                        f"nice {original_nice} → {nice_value}"
                    )
                    
                except psutil.AccessDenied:
                    results[key] = False
                    logger.warning(f"Access denied setting priority for {name} (PID {pid})")
                    
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                # Process ended during iteration
                continue
            except Exception as e:
                logger.debug(f"Error processing {proc}: {e}")
                continue
        
        logger.info(
            f"Priority adjustment complete: "
            f"{sum(results.values())}/{len(results)} processes modified to level {level.name}"
        )
        return results
    
    def restore_priorities(self, only_pids: Optional[List[int]] = None) -> Dict[str, bool]:
        """Restore all or specific processes to original priority.
        
        Args:
            only_pids: If provided, only restore these PIDs. Otherwise restores all.
            
        Returns:
            Dict mapping "name:pid" to success status.
        """
        results: Dict[str, bool] = {}
        
        pids_to_restore = only_pids or list(self._modified_processes.keys())
        
        for pid in pids_to_restore:
            if pid not in self._modified_processes:
                continue
                
            state = self._modified_processes[pid]
            key = f"{state.name}:{pid}"
            
            try:
                proc = psutil.Process(pid)
                
                # Restore nice value
                proc.nice(state.original_nice)
                
                # Restore ionice if we had it
                if state.original_ionice is not None and hasattr(proc, 'ionice'):
                    try:
                        proc.ionice(state.original_ionice)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass  # ionice restoration is optional
                
                results[key] = True
                del self._modified_processes[pid]
                logger.info(
                    f"Restored priority of {state.name} (PID {pid}): "
                    f"nice → {state.original_nice}"
                )
                
            except psutil.NoSuchProcess:
                # Process ended, just remove from tracking
                del self._modified_processes[pid]
                results[key] = True  # Consider this a success
                
            except psutil.AccessDenied:
                results[key] = False
                logger.warning(f"Access denied restoring priority for {state.name} (PID {pid})")
                
            except Exception as e:
                results[key] = False
                logger.error(f"Error restoring priority for {state.name} (PID {pid}): {e}")
        
        logger.info(f"Priority restoration complete: {sum(results.values())}/{len(results)} restored")
        return results
    
    def get_modified_processes(self) -> Dict[int, ProcessPriorityState]:
        """Get dictionary of currently modified processes.
        
        Returns:
            Dict mapping PID to ProcessPriorityState.
        """
        # Clean up any processes that no longer exist
        current_pids = list(self._modified_processes.keys())
        for pid in current_pids:
            if not psutil.pid_exists(pid):
                del self._modified_processes[pid]
        
        return self._modified_processes.copy()
    
    def detect_cpu_spikes(
        self,
        threshold_percent: float = 50.0,
        sample_interval: float = 0.5,
        min_samples: int = 3,
    ) -> List[Tuple[str, float]]:
        """Detect processes with high CPU usage that might be candidates for deprioritization.
        
        This scans for processes not in the known lists that are consuming
        significant CPU, allowing the system to suggest new apps to add.
        
        Args:
            threshold_percent: CPU usage percentage threshold.
            sample_interval: Time to measure CPU usage over (seconds).
            min_samples: Minimum samples to confirm spike (reduces false positives).
            
        Returns:
            List of (process_name, avg_cpu_percent) tuples for candidate apps.
        """
        candidates: Dict[str, List[float]] = {}
        known_apps = self.get_low_priority_apps() | PROTECTED_APPS
        
        # Take multiple samples to reduce false positives
        for _ in range(min_samples):
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    cpu = proc.cpu_percent(interval=sample_interval / min_samples)
                    name = proc.info['name'].lower()
                    
                    if cpu > threshold_percent and name not in known_apps:
                        if name not in candidates:
                            candidates[name] = []
                        candidates[name].append(cpu)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        
        # Filter to apps that spiked consistently
        result = []
        for name, cpus in candidates.items():
            if len(cpus) >= min_samples:
                avg_cpu = sum(cpus) / len(cpus)
                result.append((name, avg_cpu))
                logger.debug(f"Detected potential spike app: {name} (avg {avg_cpu:.1f}% CPU)")
        
        return sorted(result, key=lambda x: x[1], reverse=True)
    
    def suggest_low_priority_app(self, app_name: str, reason: str = "") -> None:
        """Add app to suggestions file for user review.
        
        Suggestions are stored separately from the config and must be
        explicitly approved by the user to be added to the active list.
        
        Args:
            app_name: App name to suggest.
            reason: Reason for the suggestion (e.g., "High CPU during idle").
        """
        suggestions = self._load_suggestions()
        app_key = app_name.lower()
        
        if app_key not in suggestions:
            suggestions[app_key] = {
                "suggested_at": datetime.now().isoformat(),
                "reason": reason,
                "occurrences": 1,
                "last_seen": datetime.now().isoformat(),
            }
        else:
            suggestions[app_key]["occurrences"] += 1
            suggestions[app_key]["last_seen"] = datetime.now().isoformat()
            if reason and reason not in suggestions[app_key].get("reason", ""):
                suggestions[app_key]["reason"] += f"; {reason}"
        
        self._save_suggestions(suggestions)
        logger.info(f"Suggested '{app_name}' for low priority list: {reason}")
    
    def _load_suggestions(self) -> Dict:
        """Load suggestions from file."""
        if self.suggestions_file.exists():
            try:
                with open(self.suggestions_file) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def _save_suggestions(self, data: Dict) -> None:
        """Save suggestions to file."""
        try:
            with open(self.suggestions_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save suggestions: {e}")
    
    def get_suggestions(self) -> Dict:
        """Get current app suggestions for user review.
        
        Returns:
            Dict mapping app names to suggestion details.
        """
        return self._load_suggestions()
    
    def approve_suggestion(self, app_name: str) -> bool:
        """Approve a suggestion, moving it to the active custom apps list.
        
        Args:
            app_name: App name to approve.
            
        Returns:
            True if approved, False if not found in suggestions.
        """
        suggestions = self._load_suggestions()
        app_key = app_name.lower()
        
        if app_key in suggestions:
            self.add_custom_app(app_key)
            del suggestions[app_key]
            self._save_suggestions(suggestions)
            logger.info(f"Approved suggestion '{app_name}' - added to custom apps")
            return True
        return False
    
    def reject_suggestion(self, app_name: str) -> bool:
        """Reject a suggestion, removing it from suggestions.
        
        Args:
            app_name: App name to reject.
            
        Returns:
            True if rejected, False if not found.
        """
        suggestions = self._load_suggestions()
        app_key = app_name.lower()
        
        if app_key in suggestions:
            del suggestions[app_key]
            self._save_suggestions(suggestions)
            logger.info(f"Rejected suggestion '{app_name}'")
            return True
        return False
    
    def cleanup(self) -> None:
        """Restore all priorities and cleanup resources.
        
        Should be called when shutting down the priority manager.
        """
        if self._modified_processes:
            logger.info("Cleaning up: restoring all modified process priorities")
            self.restore_priorities()
        
        logger.info("ProcessPriorityManager cleanup complete")
