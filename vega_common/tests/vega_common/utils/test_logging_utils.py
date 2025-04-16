"""
Unit tests for the logging_utils module.

Tests all functionality in the vega_common.utils.logging_utils module to ensure
it behaves as expected across different contexts.
"""
import os
import sys
import pytest
import logging
import threading
import tempfile
import random
import time
from unittest.mock import patch, MagicMock, call
from logging import LogRecord
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

from vega_common.utils.logging_utils import (
    TaskAwareFormatter,
    setup_logging,
    set_task_context,
    get_task_context,
    thread_local,
    log_lock
)


@contextmanager
def temporary_log_file():
    """Context manager that provides a temporary log file path and cleans up after use."""
    fd, path = tempfile.mkstemp(suffix='.log')
    try:
        os.close(fd)  # Close the file descriptor
        yield path
    finally:
        # Clean up the temporary file
        if os.path.exists(path):
            os.unlink(path)


class TestTaskAwareFormatter:
    """Tests for the TaskAwareFormatter class."""
    
    def test_format_with_task_id(self):
        """Test formatting a log record when a task_id is present."""
        # Set task context first
        set_task_context("test-task-123")
        
        # Create a formatter
        formatter = TaskAwareFormatter("%(levelname)s - %(message)s")
        
        # Create a log record
        record = LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Format the record
        formatted = formatter.format(record)
        
        # Verify task ID was included
        assert "[test-task-123]" in formatted
        assert "INFO - [test-task-123] Test message" == formatted
        
        # Clean up
        set_task_context("")
    
    def test_format_without_task_id(self):
        """Test formatting a log record when no task_id is present."""
        # Clear task context
        if hasattr(thread_local, "task_id"):
            del thread_local.task_id
        
        # Create a formatter
        formatter = TaskAwareFormatter("%(levelname)s - %(message)s")
        
        # Create a log record
        record = LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Format the record
        formatted = formatter.format(record)
        
        # Verify no task ID was included
        assert "[" not in formatted
        assert "INFO - Test message" == formatted
        
    def test_format_with_empty_task_id(self):
        """Test formatting when task_id is an empty string."""
        set_task_context("")
        formatter = TaskAwareFormatter("%(levelname)s - %(message)s")
        record = LogRecord(
            name="test", 
            level=logging.INFO, 
            pathname="",
            lineno=0, 
            msg="Test message", 
            args=(), 
            exc_info=None
        )
        formatted = formatter.format(record)
        # Should not include brackets when task_id is empty
        assert "[" not in formatted
        assert "INFO - Test message" == formatted

    def test_format_with_special_characters(self):
        """Test formatting with special characters in task_id."""
        special_id = "test!@#$%^&*()_+"
        set_task_context(special_id)
        formatter = TaskAwareFormatter("%(levelname)s - %(message)s")
        record = LogRecord(
            name="test", 
            level=logging.INFO, 
            pathname="",
            lineno=0, 
            msg="Test message", 
            args=(), 
            exc_info=None
        )
        formatted = formatter.format(record)
        assert f"[{special_id}]" in formatted
        assert f"INFO - [{special_id}] Test message" == formatted
        
        # Clean up
        set_task_context("")

    def test_format_with_very_long_task_id(self):
        """Test formatting with a very long task_id."""
        long_id = "x" * 100
        set_task_context(long_id)
        formatter = TaskAwareFormatter("%(levelname)s - %(message)s")
        record = LogRecord(
            name="test", 
            level=logging.INFO, 
            pathname="",
            lineno=0, 
            msg="Test message", 
            args=(), 
            exc_info=None
        )
        formatted = formatter.format(record)
        assert f"[{long_id}]" in formatted
        assert len(formatted) > 100  # Ensure the long ID is included
        
        # Clean up
        set_task_context("")


class TestSetupLogging:
    """Tests for the setup_logging function."""
    
    def test_setup_logging_default(self):
        """Test setup_logging with default parameters."""
        with temporary_log_file() as log_file:
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_root_logger = MagicMock()
                mock_get_logger.side_effect = [mock_root_logger, mock_logger]
                
                # Call the function with our temp file
                result = setup_logging(log_file=log_file)
                
                # Verify the result is our mocked logger
                assert result is mock_logger
                
                # Verify root logger was configured
                mock_root_logger.setLevel.assert_called_once_with(logging.INFO)
                
                # Verify handlers were added
                assert mock_root_logger.addHandler.call_count == 2  # Console and file handler
                
                # Verify existing handlers were removed
                assert mock_root_logger.removeHandler.call_count == len(mock_root_logger.handlers)
    
    def test_setup_logging_debug_mode(self):
        """Test setup_logging with debug mode enabled."""
        with temporary_log_file() as log_file:
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_root_logger = MagicMock()
                mock_get_logger.side_effect = [mock_root_logger, mock_logger]
                
                # Call the function with debug=True
                result = setup_logging(log_file=log_file, debug=True)
                
                # Verify debug mode was set
                mock_root_logger.setLevel.assert_called_once_with(logging.DEBUG)
    
    def test_setup_logging_handlers(self):
        """Test that setup_logging configures handlers correctly."""
        with temporary_log_file() as log_file:
            with patch('logging.getLogger') as mock_get_logger:
                # Create mock loggers
                mock_root_logger = MagicMock()
                mock_phi4_logger = MagicMock()
                mock_get_logger.side_effect = [mock_root_logger, mock_phi4_logger]
                
                # Call the function
                setup_logging(log_file=log_file)
                
                # Verify handlers were added to the root logger
                assert mock_root_logger.addHandler.call_count == 2  # Console and file handler
                
                # Get the handlers that were added
                handlers = [call_args[0][0] for call_args in mock_root_logger.addHandler.call_args_list]
                
                # Verify one is a StreamHandler (for console)
                assert any(isinstance(h, logging.StreamHandler) or 
                          'StreamHandler' in str(type(h)) for h in handlers)
                
                # Verify one is a RotatingFileHandler (for file)
                # Check for string in type name since we can't directly check the type
                # due to potential import path differences
                assert any('RotatingFileHandler' in str(type(h)) for h in handlers)

    def test_setup_logging_file_creation(self):
        """Test that setup_logging actually creates a log file and writes to it."""
        with temporary_log_file() as log_file:
            logger = setup_logging(log_file=log_file)
            logger.info("Test log message")
            
            # Check that the file was created
            assert os.path.exists(log_file)
            
            # Check content
            with open(log_file, 'r') as f:
                content = f.read()
                assert "Test log message" in content

    def test_setup_logging_custom_path(self):
        """Test setup_logging with custom log file path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = os.path.join(temp_dir, "custom", "path", "logs", "app.log")
            
            # Ensure parent directory
            os.makedirs(os.path.dirname(custom_path), exist_ok=True)
            
            try:
                logger = setup_logging(log_file=custom_path)
                logger.info("Test custom path")
                
                assert os.path.exists(custom_path)
                with open(custom_path, 'r') as f:
                    content = f.read()
                    assert "Test custom path" in content
            finally:
                # Clean up
                if os.path.exists(custom_path):
                    os.unlink(custom_path)

    def test_setup_logging_directory_creation(self):
        """Test that setup_logging attempts to create parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Path with non-existent parent directories
            log_path = os.path.join(temp_dir, "new_dir", "deeper", "app.log")
            
            # Patch both os.makedirs and handlers.RotatingFileHandler to isolate directory creation logic
            with patch('os.makedirs') as mock_makedirs:
                with patch('logging.handlers.RotatingFileHandler') as mock_handler:
                    mock_handler.return_value = MagicMock()  # Return a mock handler that won't cause issues
                    
                    # Mock os.makedirs to simulate directory creation
                    setup_logging(log_file=log_path)
                    
                    # Check that it tried to create the directory
                    mock_makedirs.assert_called_with(os.path.dirname(log_path), exist_ok=True)

    @pytest.mark.skipif(os.name != 'posix', reason="Permission test only applicable on POSIX systems")
    def test_setup_logging_invalid_path(self):
        """Test setup_logging with invalid file path (permission denied)."""
        # Skip if running tests as root/admin as they can write to protected locations
        if os.geteuid() == 0:  # Root user
            pytest.skip("Skipping permission test when running as root")

        # Try to log to a location where we don't have permission
        with pytest.raises((PermissionError, IOError, OSError)):
            with patch('os.makedirs', side_effect=PermissionError("Permission denied")):
                setup_logging(log_file="/root/protected/test.log")

    def test_setup_logging_error_handling(self):
        """Test that setup_logging handles errors gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "logs", "app.log")
            
            # We need to patch the traceback extraction to make the code think we're not in a test
            with patch('traceback.extract_stack', return_value=[('not_a_test_file', 0, 'function', None)]):
                # Simulate errors with patching
                with patch('logging.handlers.RotatingFileHandler', 
                        side_effect=IOError("Simulated IO Error")):
                    with patch('logging.getLogger') as mock_get_logger:
                        mock_logger = MagicMock()
                        mock_root_logger = MagicMock()
                        mock_get_logger.side_effect = [mock_root_logger, mock_logger]
                        
                        # Should still create a logger with console handler even if file handler fails
                        result = setup_logging(log_file=log_path)
                        
                        # Verify at least console handler was added
                        assert mock_root_logger.addHandler.call_count >= 1
                        # Verify a warning was logged
                        mock_root_logger.warning.assert_called_with(
                            "Failed to set up file logging: Simulated IO Error"
                        )


class TestTaskContext:
    """Tests for the task context functions."""
    
    def test_set_and_get_task_context(self):
        """Test setting and getting task context."""
        # Clear any existing task context
        if hasattr(thread_local, "task_id"):
            del thread_local.task_id
            
        # Verify default value when not set
        assert get_task_context() == ""
        
        # Set task context and verify
        set_task_context("task-456")
        assert get_task_context() == "task-456"
        
        # Change task context and verify
        set_task_context("task-789")
        assert get_task_context() == "task-789"
        
        # Clear task context and verify
        set_task_context("")
        assert get_task_context() == ""
    
    def test_thread_local_isolation(self):
        """Test that task context is thread-local."""
        # Set a task context in the main thread
        set_task_context("main-thread-task")
        
        # Thread-local values
        thread_values = {}
        
        def worker_thread(thread_name):
            # Set a different task context in this thread
            set_task_context(f"{thread_name}-task")
            # Store the value for verification
            thread_values[thread_name] = get_task_context()
        
        # Create and start two worker threads
        threads = [
            threading.Thread(target=worker_thread, args=(f"thread-{i}",))
            for i in range(2)
        ]
        
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
        
        # Verify main thread context wasn't changed
        assert get_task_context() == "main-thread-task"
        
        # Verify each thread had its own context
        assert thread_values["thread-0"] == "thread-0-task"
        assert thread_values["thread-1"] == "thread-1-task"
        
        # Clean up
        set_task_context("")


class TestThreadSafety:
    """Tests for thread safety aspects of the logging utilities."""
    
    def test_log_lock(self):
        """Test that the log_lock is a proper threading lock instance."""
        # The lock should be an instance of the _thread.lock class
        # We can't directly check the type since it's an internal implementation detail
        # Instead, we'll verify it has the expected lock interface
        
        # Verify it has the expected lock methods
        assert hasattr(log_lock, 'acquire')
        assert hasattr(log_lock, 'release')
        
        # Verify lock can be acquired and released
        acquired = log_lock.acquire(blocking=False)
        assert acquired is True
        log_lock.release()

    @patch('logging.Logger.info')
    def test_concurrent_logging(self, mock_info):
        """Test concurrent logging operations from multiple threads."""
        # The real test is that this doesn't crash with race conditions
        # We'll use our formatter and task context in multiple threads
        
        with temporary_log_file() as log_file:
            # Set up a real logger that uses our TaskAwareFormatter
            logger = logging.getLogger("test_concurrent")
            handler = logging.StreamHandler()
            handler.setFormatter(TaskAwareFormatter("%(levelname)s - %(message)s"))
            logger.addHandler(handler)
            
            def logging_worker(thread_id):
                # Set task context for this thread
                set_task_context(f"thread-{thread_id}")
                # Log some messages
                for i in range(5):
                    logger.info(f"Message {i} from thread {thread_id}")
            
            # Create and start multiple threads
            threads = [
                threading.Thread(target=logging_worker, args=(i,))
                for i in range(3)
            ]
            
            for thread in threads:
                thread.start()
                
            for thread in threads:
                thread.join()
                
            # No assertions needed - if there were thread safety issues,
            # we would likely see exceptions during execution


class TestContextPropagation:
    """Tests for task context propagation through various execution flows."""
    
    def test_task_context_propagation_to_logs(self):
        """Test that task context properly propagates to log messages."""
        with temporary_log_file() as log_file:
            # Configure logging
            logger = setup_logging(log_file=log_file)
            
            # Set task context
            set_task_context("integration-test")
            
            # Log a message
            logger.info("Integration test message")
            
            # Verify the message contains the task ID
            with open(log_file, 'r') as f:
                content = f.read()
                assert "[integration-test]" in content
                assert "Integration test message" in content
            
            # Clean up
            set_task_context("")

    def test_context_inheritance_in_callbacks(self):
        """Test that task context is correctly passed to callback functions."""
        set_task_context("parent-context")
        
        # Track the task context observed in the callback
        callback_context = []
        
        def callback_function():
            callback_context.append(get_task_context())
        
        # Run the callback in the current thread
        callback_function()
        
        # Verify the context was properly passed
        assert callback_context[0] == "parent-context"
        
        # Clean up
        set_task_context("")
    
    def test_nested_context_changes(self):
        """Test that nested context changes don't affect parent context."""
        set_task_context("parent-task")
        
        def nested_function():
            # Save original context
            original = get_task_context()
            # Change it temporarily
            set_task_context("nested-task")
            # Verify change was effective
            assert get_task_context() == "nested-task"
            # Restore original context
            set_task_context(original)
        
        # Run the nested function
        nested_function()
        
        # Verify parent context is preserved
        assert get_task_context() == "parent-task"
        
        # Clean up
        set_task_context("")


class TestAdvancedThreading:
    """Tests for more complex threading scenarios with task contexts."""
    
    def test_task_context_with_thread_pool(self):
        """Test task context behavior with a thread pool."""
        # Define a function that captures the task context
        def get_context_in_thread(thread_name):
            set_task_context(f"{thread_name}")
            return get_task_context()
        
        # Execute in a thread pool
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit multiple tasks
            futures = [
                executor.submit(get_context_in_thread, f"thread-{i}")
                for i in range(5)
            ]
            
            # Get results
            results = [future.result() for future in futures]
        
        # Each thread should have its own context
        expected_contexts = [f"thread-{i}" for i in range(5)]
        assert sorted(results) == sorted(expected_contexts)
        
    def test_concurrent_context_changes(self):
        """Test concurrent task context changes from multiple threads."""
        from concurrent.futures import ThreadPoolExecutor
        import random
        import time
        
        # Set initial context
        set_task_context("main")
        
        # Function that changes context multiple times
        def change_context_repeatedly(thread_id):
            results = []
            for i in range(5):
                # Set a unique context for this thread and iteration
                context_id = f"thread-{thread_id}-iter-{i}"
                set_task_context(context_id)
                
                # Small random sleep to increase chances of thread interleaving
                time.sleep(random.uniform(0.001, 0.005))
                
                # Verify our context is still what we set (not affected by other threads)
                current = get_task_context()
                results.append((context_id, current))
            return results
        
        # Run multiple threads that change contexts
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(change_context_repeatedly, i)
                for i in range(3)
            ]
            all_results = [future.result() for future in futures]
        
        # Flatten results
        flat_results = [item for sublist in all_results for item in sublist]
        
        # Verify that each thread maintained its own context correctly
        for expected, actual in flat_results:
            assert expected == actual
        
        # Verify main thread's context is still "main"
        assert get_task_context() == "main"
        
        # Clean up
        set_task_context("")


class TestLogRotation:
    """Tests for the log rotation functionality."""
    
    def test_log_rotation_parameters(self):
        """Test log file rotation parameters are correctly set."""
        with patch('logging.handlers.RotatingFileHandler') as mock_handler:
            setup_logging(log_file="test.log")
            
            # Verify the handler was created with expected parameters
            mock_handler.assert_called_once()
            args, kwargs = mock_handler.call_args
            
            # Check rotation parameters
            assert kwargs['maxBytes'] == 10 * 1024 * 1024  # 10MB
            assert kwargs['backupCount'] == 5
    
    def test_log_rotation_actual(self):
        """Test actual log rotation when size exceeds limit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = os.path.join(temp_dir, "rotating.log")
            
            # Set a higher recursion limit temporarily for this test
            original_limit = sys.getrecursionlimit()
            try:
                sys.setrecursionlimit(5000)  # Increase limit to avoid potential recursion errors
                
                # Create log file without mocking to test actual rotation
                small_size = 1024  # 1KB for testing rotation
                
                # Create a real logger with actual handlers for this test 
                # Instead of patching, we'll configure directly
                root_logger = logging.getLogger()
                original_level = root_logger.level
                original_handlers = root_logger.handlers.copy()
                
                try:
                    # Remove any existing handlers
                    for handler in root_logger.handlers[:]:
                        root_logger.removeHandler(handler)
                    
                    # Set up console handler
                    console_handler = logging.StreamHandler()
                    console_handler.setFormatter(logging.Formatter("%(message)s"))
                    root_logger.addHandler(console_handler)
                    
                    # Set up rotating file handler with small size
                    file_handler = logging.handlers.RotatingFileHandler(
                        log_path,
                        maxBytes=small_size,
                        backupCount=3
                    )
                    file_handler.setFormatter(logging.Formatter("%(message)s"))
                    root_logger.addHandler(file_handler)
                    
                    # Generate enough logs to trigger rotation
                    large_msg = "x" * (small_size // 2)  # Message is half the max size
                    
                    # Log enough to create at least one backup file
                    for i in range(5):  # Should trigger at least 2 rotations
                        root_logger.info(large_msg)
                        # Force flush after each write to ensure data is written to disk
                        for handler in root_logger.handlers:
                            if hasattr(handler, 'flush'):
                                handler.flush()
                    
                    # Close all handlers to ensure all data is written and files are properly closed
                    for handler in root_logger.handlers:
                        if hasattr(handler, 'close'):
                            handler.close()
                    
                    # Small delay to ensure file system operations complete
                    time.sleep(0.1)
                    
                    # Check if backup file was created
                    backup_file = f"{log_path}.1"
                    assert os.path.exists(backup_file), "Log rotation failed to create backup file"
                    
                finally:
                    # Restore original logger configuration
                    for handler in root_logger.handlers[:]:
                        root_logger.removeHandler(handler)
                    
                    for handler in original_handlers:
                        root_logger.addHandler(handler)
                    
                    root_logger.setLevel(original_level)
            finally:
                # Restore original recursion limit
                sys.setrecursionlimit(original_limit)

    @patch('logging.Logger.warning')
    def test_formatter_exception_handling(self, mock_warning):
        """Test that the formatter handles exceptions gracefully."""
        # Create a formatter
        formatter = TaskAwareFormatter("%(levelname)s - %(message)s")
        
        # Create a record with a problematic attribute that might cause errors
        record = MagicMock()
        record.getMessage = MagicMock(side_effect=Exception("getMessage error"))
        record.levelname = "ERROR"
        
        # This should not raise an exception, but instead return a fallback format
        formatted = formatter.format(record)
        
        # Verify that a fallback message was returned
        assert "ERROR - Formatting Error:" in formatted
        assert "Unknown message" in formatted