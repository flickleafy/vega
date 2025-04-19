"""
Device monitoring utilities for the Vega project.

This module provides base classes and interfaces for implementing device 
monitoring functionality across different hardware components in a consistent way.
"""
import threading
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable, Optional, Union

from vega_common.utils.device_status import DeviceStatus


class DeviceMonitor(ABC):
    """
    Abstract base class for device monitors.
    
    This class defines the interface for all device monitors in the Vega system,
    ensuring consistent behavior and interoperability.
    
    Attributes:
        device_id (str): Unique identifier for the monitored device.
        device_type (str): Type of the monitored device.
        status (DeviceStatus): Current status of the device.
        monitoring_interval (float): Interval between status updates in seconds.
        is_monitoring (bool): Flag indicating if monitoring is active.
        monitor_thread (threading.Thread): Thread running the monitoring loop.
    """
    
    def __init__(self, 
                 device_id: str, 
                 device_type: str, 
                 device_name: str = None,
                 monitoring_interval: float = 3.0,
                 tracked_properties: List[str] = None):
        """
        Initialize a DeviceMonitor.
        
        Args:
            device_id (str): Unique identifier for the monitored device.
            device_type (str): Type of the monitored device.
            monitoring_interval (float, optional): Interval between updates in seconds.
                Defaults to 3.0.
            tracked_properties (List[str], optional): List of properties to track history for.
                Defaults to None.
        """
        self.device_id = device_id
        self.device_type = device_type
        self.device_name = device_name 
        self.status = DeviceStatus(device_id, device_type)
        self.monitoring_interval = monitoring_interval
        self.is_monitoring = False
        self.monitor_thread = None
        self._stop_event = threading.Event()
        
        # Register tracked properties if provided
        if tracked_properties:
            for prop in tracked_properties:
                self.status.register_tracked_property(prop)
    
    @abstractmethod
    def update_status(self) -> None:
        """
        Update the device status with fresh data.
        
        This method should be implemented by subclasses to perform
        the actual status update for the specific device type.
        """
        pass
    
    def start_monitoring(self) -> None:
        """
        Start the monitoring thread if not already running.
        """
        if not self.is_monitoring:
            self._stop_event.clear()
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            logging.info(f"Started monitoring for {self.device_type} device: {self.device_id}")
    
    def stop_monitoring(self) -> None:
        """
        Stop the monitoring thread if running.
        """
        if self.is_monitoring:
            self._stop_event.set()
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2.0)  # Wait up to 2 seconds for thread to finish
            self.is_monitoring = False
            logging.info(f"Stopped monitoring for {self.device_type} device: {self.device_id}")
    
    def _monitoring_loop(self) -> None:
        """
        Main monitoring loop that updates status at regular intervals.
        """
        while not self._stop_event.is_set():
            try:
                self.update_status()
            except Exception as e:
                logging.error(f"Error updating {self.device_type} status: {str(e)}")
            
            # Wait for the next update interval or until stop is requested
            self._stop_event.wait(self.monitoring_interval)
    
    def get_status_dict(self) -> Dict[str, Any]:
        """
        Get the current device status as a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of device status.
        """
        return self.status.to_dict()


