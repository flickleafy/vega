"""
CPU thermal specifications database and threshold calculator.

Provides per-CPU-model temperature thresholds based on manufacturer specifications.
Supports AMD Ryzen and Intel Core processors with automatic model detection.
"""

import re
from dataclasses import dataclass
from typing import Optional, List

from vega_common.utils.logging_utils import get_module_logger

logger = get_module_logger("vega_common/utils/cpu_thermal_specs")


@dataclass
class CpuThermalSpec:
    """Thermal specifications for a CPU model.
    
    Attributes:
        model_pattern: Regex pattern to match CPU model name
        tjmax: Maximum junction temperature in °C
        throttle_temp: Temperature where throttling begins in °C
        manufacturer: "AMD" or "Intel"
    """
    model_pattern: str
    tjmax: float
    throttle_temp: float
    manufacturer: str
    
    @property
    def hot_threshold(self) -> float:
        """Temperature considered 'hot' - 90% of tjmax.
        
        At this level, aggressive power saving should be applied.
        """
        return self.tjmax * 0.75
    
    @property
    def warm_threshold(self) -> float:
        """Temperature considered 'warm' - 80% of tjmax.
        
        At this level, moderate power saving should be considered.
        """
        return self.tjmax * 0.70
    
    @property
    def cool_threshold(self) -> float:
        """Temperature considered 'cool' - 60% of tjmax.
        
        Below this level, full performance is safe.
        """
        return self.tjmax * 0.60
    
    def get_thresholds(self) -> dict:
        """Get all temperature thresholds as a dictionary.
        
        Returns:
            Dict with 'hot', 'warm', 'cool' thresholds and 'tjmax'.
        """
        return {
            "tjmax": self.tjmax,
            "throttle": self.throttle_temp,
            "hot": self.hot_threshold,
            "warm": self.warm_threshold,
            "cool": self.cool_threshold,
        }


# CPU Thermal Database - ordered from most specific to most general patterns
# Patterns are matched in order, so more specific models should come first
CPU_THERMAL_DATABASE: List[CpuThermalSpec] = [
    # === AMD Ryzen 9000 Series (Zen 5) ===
    CpuThermalSpec(r"Ryzen 9 9\d{3}X3D", tjmax=89, throttle_temp=89, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 9 9\d{3}X?", tjmax=95, throttle_temp=95, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 7 9\d{3}X?", tjmax=95, throttle_temp=95, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 5 9\d{3}X?", tjmax=95, throttle_temp=95, manufacturer="AMD"),
    
    # === AMD Ryzen 7000 Series (Zen 4) ===
    CpuThermalSpec(r"Ryzen 9 7950X3D", tjmax=89, throttle_temp=89, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 9 7900X3D", tjmax=89, throttle_temp=89, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 7 7800X3D", tjmax=89, throttle_temp=89, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 9 7\d{3}X?", tjmax=95, throttle_temp=95, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 7 7\d{3}X?", tjmax=95, throttle_temp=95, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 5 7\d{3}X?", tjmax=95, throttle_temp=95, manufacturer="AMD"),
    
    # === AMD Ryzen 5000 Series (Zen 3) ===
    CpuThermalSpec(r"Ryzen 9 5950X", tjmax=90, throttle_temp=90, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 9 5900X", tjmax=90, throttle_temp=90, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 7 5800X3D", tjmax=90, throttle_temp=90, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 7 5800X", tjmax=90, throttle_temp=90, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 7 5700X", tjmax=90, throttle_temp=90, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 5 5600X", tjmax=95, throttle_temp=95, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 5 5600", tjmax=95, throttle_temp=95, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 5 5500", tjmax=95, throttle_temp=95, manufacturer="AMD"),
    
    # === AMD Ryzen 3000 Series (Zen 2) ===
    CpuThermalSpec(r"Ryzen 9 3950X", tjmax=95, throttle_temp=95, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 9 3900X", tjmax=95, throttle_temp=95, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 7 3800X", tjmax=95, throttle_temp=95, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 7 3700X", tjmax=95, throttle_temp=95, manufacturer="AMD"),
    CpuThermalSpec(r"Ryzen 5 3600X?", tjmax=95, throttle_temp=95, manufacturer="AMD"),
    
    # === Intel 14th Gen (Raptor Lake Refresh) ===
    CpuThermalSpec(r"i9-14\d{3}K", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    CpuThermalSpec(r"i7-14\d{3}K?", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    CpuThermalSpec(r"i5-14\d{3}K?", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    CpuThermalSpec(r"i3-14\d{3}", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    
    # === Intel 13th Gen (Raptor Lake) ===
    CpuThermalSpec(r"i9-13\d{3}K", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    CpuThermalSpec(r"i7-13\d{3}K?", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    CpuThermalSpec(r"i5-13\d{3}K?", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    CpuThermalSpec(r"i3-13\d{3}", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    
    # === Intel 12th Gen (Alder Lake) ===
    CpuThermalSpec(r"i9-12\d{3}K", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    CpuThermalSpec(r"i7-12\d{3}K?", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    CpuThermalSpec(r"i5-12\d{3}K?", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    CpuThermalSpec(r"i3-12\d{3}", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    
    # === Intel 11th Gen (Rocket Lake / Tiger Lake) ===
    CpuThermalSpec(r"i9-11\d{3}", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    CpuThermalSpec(r"i7-11\d{3}", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    CpuThermalSpec(r"i5-11\d{3}", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    
    # === Intel 10th Gen (Comet Lake) ===
    CpuThermalSpec(r"i9-10\d{3}", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    CpuThermalSpec(r"i7-10\d{3}", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    CpuThermalSpec(r"i5-10\d{3}", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    
    # === Fallback patterns (must be last) ===
    # Generic AMD Ryzen pattern
    CpuThermalSpec(r"Ryzen", tjmax=90, throttle_temp=90, manufacturer="AMD"),
    # Generic Intel Core pattern
    CpuThermalSpec(r"Core.*i\d", tjmax=100, throttle_temp=100, manufacturer="Intel"),
    # Generic Intel pattern
    CpuThermalSpec(r"Intel", tjmax=100, throttle_temp=100, manufacturer="Intel"),
]

# Default spec when CPU cannot be identified - conservative values
DEFAULT_THERMAL_SPEC = CpuThermalSpec(
    model_pattern="Unknown",
    tjmax=85,  # Conservative default
    throttle_temp=85,
    manufacturer="Unknown"
)


def detect_cpu_model() -> str:
    """Detect CPU model from /proc/cpuinfo.
    
    Returns:
        str: CPU model name, or "Unknown" if detection fails.
    
    Complexity: O(N) where N is number of lines in /proc/cpuinfo.
    """
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("model name"):
                    model = line.split(":", 1)[1].strip()
                    logger.debug(f"Detected CPU model: {model}")
                    return model
    except FileNotFoundError:
        logger.warning("Could not read /proc/cpuinfo - file not found")
    except PermissionError:
        logger.warning("Could not read /proc/cpuinfo - permission denied")
    except Exception as e:
        logger.warning(f"Could not detect CPU model: {e}")
    
    return "Unknown"


def get_thermal_spec(cpu_model: Optional[str] = None) -> CpuThermalSpec:
    """Get thermal specification for the given or detected CPU model.
    
    Args:
        cpu_model: CPU model name string. If None, auto-detects from system.
        
    Returns:
        CpuThermalSpec: Matching thermal specification or default if no match.
        
    Complexity: O(D) where D is number of entries in CPU_THERMAL_DATABASE.
    """
    if cpu_model is None:
        cpu_model = detect_cpu_model()
    
    for spec in CPU_THERMAL_DATABASE:
        if re.search(spec.model_pattern, cpu_model, re.IGNORECASE):
            logger.info(
                f"Matched CPU '{cpu_model}' to thermal spec: "
                f"tjmax={spec.tjmax}°C, hot={spec.hot_threshold:.1f}°C, "
                f"warm={spec.warm_threshold:.1f}°C"
            )
            return spec
    
    logger.warning(
        f"No thermal spec found for '{cpu_model}', using conservative defaults: "
        f"tjmax={DEFAULT_THERMAL_SPEC.tjmax}°C"
    )
    return DEFAULT_THERMAL_SPEC


def get_thermal_spec_for_model(model_name: str) -> Optional[CpuThermalSpec]:
    """Get thermal spec for a specific model name without falling back to defaults.
    
    Args:
        model_name: Exact or partial CPU model name to search for.
        
    Returns:
        CpuThermalSpec if found, None if no match.
        
    Complexity: O(D) where D is number of entries in CPU_THERMAL_DATABASE.
    """
    for spec in CPU_THERMAL_DATABASE:
        if re.search(spec.model_pattern, model_name, re.IGNORECASE):
            return spec
    return None


def list_supported_cpus() -> List[str]:
    """List all CPU patterns in the thermal database.
    
    Returns:
        List of regex patterns for supported CPU models.
    """
    return [spec.model_pattern for spec in CPU_THERMAL_DATABASE]
