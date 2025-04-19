"""
Unit tests for process_utils.py module.

This test suite provides comprehensive tests for the process utility
functions, with mock objects for psutil to avoid system dependencies.
"""

import pytest
import psutil
from unittest.mock import patch, MagicMock
from typing import Set, Dict, Any, List

from vega_common.utils.process_utils import (
    similar_string_list,
    get_process_list,
    detect_balance_apps,
    detect_performance_apps,
    ignore_list,
    strict_ignore_list,
    BALANCE_APP_LIST,
    PERFORMANCE_APP_LIST
)


class TestSimilarStringList:
    """Tests for the similar_string_list function."""
    
    def test_with_matching_ignore_substring(self):
        """Test when the string contains a substring from the ignore list."""
        # When a string contains an item from the ignore list
        result = similar_string_list("test_kworker_process", ["kworker", "other"], [])
        assert result is True

    def test_with_exact_strict_match(self):
        """Test when the string exactly matches a strict ignore item."""
        # When a string exactly matches an item from the strict_ignore list
        result = similar_string_list("sh", [], ["sh", "other"])
        assert result is True

    def test_with_no_match(self):
        """Test when the string doesn't match any ignore criteria."""
        # When a string doesn't match any item from either list
        result = similar_string_list("my_custom_process", ["system", "kernel"], ["sh", "md"])
        assert result is False
    
    def test_with_empty_ignore_lists(self):
        """Test when both ignore lists are empty."""
        # When both ignore lists are empty
        result = similar_string_list("any_process", [], [])
        assert result is False
    
    def test_with_empty_string(self):
        """Test with an empty string."""
        # When the input string is empty
        result = similar_string_list("", ["test"], ["example"])
        assert result is False


class MockProcess:
    """Mock class to simulate psutil.Process objects."""
    
    def __init__(self, name: str):
        """Initialize with a process name."""
        self.info = {'name': name}
        self._name = name
        
    def throws(self, exception):
        """Configure this mock to raise an exception when info is accessed."""
        class RaiseOnAccess:
            def __getitem__(self, _):
                raise exception
        self.info = RaiseOnAccess()
        return self


class TestGetProcessList:
    """Tests for the get_process_list function."""

    @patch('psutil.process_iter')
    def test_basic_process_filtering(self, mock_process_iter):
        """Test basic process filtering functionality."""
        # Setup process mock to return test processes
        mock_processes = [
            MockProcess("myapp"),           # Should be included
            MockProcess("browser"),         # Should be included
            MockProcess("kworker"),         # Should be excluded (in ignore_list)
            MockProcess("sh"),              # Should be excluded (in strict_ignore_list)
            MockProcess("custom_process")   # Should be included
        ]
        mock_process_iter.return_value = mock_processes
        
        # Call function
        result = get_process_list()
        
        # Verify results
        assert "myapp" in result
        assert "browser" in result
        assert "custom_process" in result
        assert "kworker" not in result
        assert "sh" not in result
        assert len(result) == 3

    @patch('psutil.process_iter')
    def test_handle_access_denied_exception(self, mock_process_iter):
        """Test handling of AccessDenied exception."""
        # Setup process mock with an exception
        mock_processes = [
            MockProcess("normal_process"),
            MockProcess("system_process").throws(psutil.AccessDenied()),
            MockProcess("another_process")
        ]
        mock_process_iter.return_value = mock_processes
        
        # Call function - should not raise exception
        result = get_process_list()
        
        # Verify the accessible processes were properly handled
        assert "normal_process" in result
        assert "another_process" in result

    @patch('psutil.process_iter')
    def test_handle_no_such_process_exception(self, mock_process_iter):
        """Test handling of NoSuchProcess exception."""
        # Setup process mock with an exception
        mock_processes = [
            MockProcess("normal_process"),
            MockProcess("zombie_process").throws(psutil.NoSuchProcess(123, "test")),
            MockProcess("another_process")
        ]
        mock_process_iter.return_value = mock_processes
        
        # Call function - should not raise exception
        result = get_process_list()
        
        # Verify the accessible processes were properly handled
        assert "normal_process" in result
        assert "another_process" in result
    
    @patch('psutil.process_iter')
    def test_handle_zombie_process_exception(self, mock_process_iter):
        """Test handling of ZombieProcess exception."""
        # Setup process mock with an exception
        mock_processes = [
            MockProcess("normal_process"),
            MockProcess("zombie").throws(psutil.ZombieProcess(123)),
            MockProcess("another_process")
        ]
        mock_process_iter.return_value = mock_processes
        
        # Call function - should not raise exception
        result = get_process_list()
        
        # Verify the accessible processes were properly handled
        assert "normal_process" in result
        assert "another_process" in result
    
    @patch('psutil.process_iter')
    def test_handle_general_psutil_error(self, mock_process_iter):
        """Test handling of general psutil.Error exceptions."""
        # Setup process mock with a general psutil error
        mock_processes = [
            MockProcess("normal_process"),
            MockProcess("error_process").throws(psutil.Error("Test error")),
            MockProcess("another_process")
        ]
        mock_process_iter.return_value = mock_processes
        
        # Call function - should not raise exception
        result = get_process_list()
        
        # Verify the accessible processes were properly handled
        assert "normal_process" in result
        assert "another_process" in result

    @patch('psutil.process_iter')
    def test_empty_process_list(self, mock_process_iter):
        """Test with an empty process list."""
        mock_process_iter.return_value = []
        
        result = get_process_list()
        
        assert isinstance(result, set)
        assert len(result) == 0

    @patch('psutil.process_iter')
    def test_case_insensitivity(self, mock_process_iter):
        """Test that process names are converted to lowercase."""
        mock_processes = [
            MockProcess("UPPERCASE_APP"),
            MockProcess("MixedCase")
        ]
        mock_process_iter.return_value = mock_processes
        
        result = get_process_list()
        
        assert "uppercase_app" in result
        assert "mixedcase" in result
        assert "UPPERCASE_APP" not in result
        assert "MixedCase" not in result


class TestDetectBalanceApps:
    """Tests for the detect_balance_apps function."""
    
    def test_detect_balance_app_present(self):
        """Test when a balance app is present in the process list."""
        # Include firefox which is in the BALANCE_APP_LIST
        process_list = {"myapp", "firefox", "background_service"}
        
        result = detect_balance_apps(process_list)
        
        assert result is True
    
    def test_detect_balance_app_absent(self):
        """Test when no balance app is present in the process list."""
        # No process matches anything in BALANCE_APP_LIST
        process_list = {"myapp", "custom_service", "background_task"}
        
        result = detect_balance_apps(process_list)
        
        assert result is False
    
    def test_with_empty_process_list(self):
        """Test with an empty process list."""
        process_list = set()
        
        result = detect_balance_apps(process_list)
        
        assert result is False
    
    def test_ensure_exact_match(self):
        """Test that substring matching is not occurring for exact matching."""
        # "fire" should not match "firefox" using exact matching
        process_list = {"myapp", "fire", "custom_service"}
        
        result = detect_balance_apps(process_list)
        
        assert result is False
        
        # Test with a partial match that should not be detected
        process_list = {"my_firefox_plugin"}  # This should not match "firefox"
        
        result = detect_balance_apps(process_list)
        
        assert result is False


class TestDetectPerformanceApps:
    """Tests for the detect_performance_apps function."""
    
    def test_detect_performance_app_present(self):
        """Test when a performance app is present in the process list."""
        # Include blender which is in the PERFORMANCE_APP_LIST
        process_list = {"myapp", "blender", "background_service"}
        
        result = detect_performance_apps(process_list)
        
        assert result is True
    
    def test_detect_performance_app_absent(self):
        """Test when no performance app is present in the process list."""
        # No process matches anything in PERFORMANCE_APP_LIST
        process_list = {"myapp", "custom_service", "background_task"}
        
        result = detect_performance_apps(process_list)
        
        assert result is False
    
    def test_with_empty_process_list(self):
        """Test with an empty process list."""
        process_list = set()
        
        result = detect_performance_apps(process_list)
        
        assert result is False
    
    def test_ensure_exact_match(self):
        """Test that substring matching is not occurring for exact matching."""
        # "steam_update" should not match "steam" using exact matching
        process_list = {"myapp", "steam_update", "custom_service"}
        
        result = detect_performance_apps(process_list)
        
        assert result is False
        
        # Test with a partial match that should not be detected  
        process_list = {"my_gimp_plugin"}  # This should not match "gimp"
        
        result = detect_performance_apps(process_list)
        
        assert result is False
        
    def test_validation_all_apps_lowercase(self):
        """Test to validate that all predefined apps are lowercase."""
        # This test ensures the app lists are properly formatted
        for app in BALANCE_APP_LIST:
            assert app == app.lower(), f"App '{app}' in BALANCE_APP_LIST is not lowercase"
            
        for app in PERFORMANCE_APP_LIST:
            assert app == app.lower(), f"App '{app}' in PERFORMANCE_APP_LIST is not lowercase"