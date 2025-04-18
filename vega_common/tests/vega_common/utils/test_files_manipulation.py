"""
Unit tests for the files_manipulation module.

Tests all functions in the vega_common.utils.files_manipulation module to ensure
they behave as expected across different contexts.
"""
import os
import shutil
import tempfile
import pytest
import json
from pathlib import Path
from vega_common.utils.files_manipulation import (
    read_file,
    write_file,
    safe_open,
    ensure_directory_exists,
    read_json_file,
    write_json_file
)


class TestFileManipulation:
    """Base class with setup/teardown for file manipulation tests."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Create and clean up a temporary directory for file tests."""
        # Setup - Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test file with content
        self.test_file_path = os.path.join(self.temp_dir, "test_file.txt")
        self.test_content = ["Line 1\n", "Line 2\n", "Line 3\n"]
        with open(self.test_file_path, 'w') as f:
            f.writelines(self.test_content)
        
        # Create a nested directory path for testing directory creation
        self.nested_dir_path = os.path.join(self.temp_dir, "nested", "dir", "path")
        
        yield  # This is where the test runs
        
        # Teardown - Remove temporary directory and all its contents
        shutil.rmtree(self.temp_dir)


class TestReadFile(TestFileManipulation):
    """Tests for the read_file function."""
    
    def test_read_existing_file(self):
        """Test read_file with an existing file."""
        result = read_file(self.test_file_path)
        assert result == self.test_content
    
    def test_read_nonexistent_file(self):
        """Test read_file with a nonexistent file raises FileNotFoundError."""
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent.txt")
        with pytest.raises(FileNotFoundError):
            read_file(nonexistent_path)
    
    def test_read_empty_file(self):
        """Test read_file with an empty file."""
        empty_file_path = os.path.join(self.temp_dir, "empty.txt")
        open(empty_file_path, 'w').close()  # Create empty file
        result = read_file(empty_file_path)
        assert result == []
    
    def test_file_without_permission(self):
        """Test read_file with a file without read permission raises PermissionError."""
        if os.name != "nt":  # Skip on Windows, which has different permission model
            no_perm_file = os.path.join(self.temp_dir, "no_permission.txt")
            with open(no_perm_file, 'w') as f:
                f.write("This is a test")
            
            # Remove read permission
            os.chmod(no_perm_file, 0o000)
            
            try:
                with pytest.raises(PermissionError):
                    read_file(no_perm_file)
            finally:
                # Restore permissions to ensure cleanup can happen
                os.chmod(no_perm_file, 0o666)


class TestWriteFile(TestFileManipulation):
    """Tests for the write_file function."""
    
    def test_write_new_file(self):
        """Test write_file with a new file."""
        new_file_path = os.path.join(self.temp_dir, "new_file.txt")
        content = ["New line 1\n", "New line 2\n"]
        write_file(new_file_path, content)
        
        # Verify file was written correctly
        with open(new_file_path, 'r') as f:
            result = f.readlines()
        
        assert result == content
    
    def test_overwrite_existing_file(self):
        """Test write_file to overwrite an existing file."""
        new_content = ["Replaced line 1\n", "Replaced line 2\n"]
        write_file(self.test_file_path, new_content)
        
        # Verify file was overwritten
        with open(self.test_file_path, 'r') as f:
            result = f.readlines()
        
        assert result == new_content
    
    def test_write_empty_content(self):
        """Test write_file with empty content."""
        empty_content_path = os.path.join(self.temp_dir, "empty_content.txt")
        write_file(empty_content_path, [])
        
        # Verify empty file was created
        with open(empty_content_path, 'r') as f:
            result = f.readlines()
        
        assert result == []
    
    def test_write_to_directory_without_permission(self):
        """Test write_file to a directory without write permission raises PermissionError."""
        if os.name != "nt":  # Skip on Windows, which has different permission model
            no_perm_dir = os.path.join(self.temp_dir, "no_perm_dir")
            os.makedirs(no_perm_dir)
            no_perm_file = os.path.join(no_perm_dir, "test.txt")
            
            # Remove write permission from directory
            os.chmod(no_perm_dir, 0o500)  # r-x permission
            
            try:
                with pytest.raises(PermissionError):
                    write_file(no_perm_file, ["Test\n"])
            finally:
                # Restore permissions to ensure cleanup can happen
                os.chmod(no_perm_dir, 0o755)


class TestSafeOpen(TestFileManipulation):
    """Tests for the safe_open context manager."""
    
    def test_read_mode(self):
        """Test safe_open in read mode."""
        with safe_open(self.test_file_path, 'r') as f:
            content = f.readlines()
        assert content == self.test_content
    
    def test_write_mode(self):
        """Test safe_open in write mode."""
        new_file_path = os.path.join(self.temp_dir, "safe_open_write.txt")
        content = ["Written with safe_open\n"]
        
        with safe_open(new_file_path, 'w') as f:
            f.writelines(content)
        
        # Verify file was written correctly
        with open(new_file_path, 'r') as f:
            result = f.readlines()
        
        assert result == content
    
    def test_nonexistent_file_read(self):
        """Test safe_open with a nonexistent file in read mode raises FileNotFoundError."""
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent_safe.txt")
        with pytest.raises(FileNotFoundError):
            with safe_open(nonexistent_path, 'r') as f:
                f.read()
    
    def test_exception_inside_context(self):
        """Test that file is closed even if an exception occurs inside the context manager."""
        try:
            with safe_open(self.test_file_path, 'r') as f:
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # The file should be closed at this point
        assert f.closed


class TestEnsureDirectoryExists(TestFileManipulation):
    """Tests for the ensure_directory_exists function."""
    
    def test_create_new_directory(self):
        """Test ensure_directory_exists with a new directory path."""
        new_dir = os.path.join(self.temp_dir, "new_dir")
        
        # Ensure directory doesn't exist before test
        assert not os.path.exists(new_dir)
        
        ensure_directory_exists(os.path.join(new_dir, "test.txt"))
        
        # Directory should now exist
        assert os.path.exists(new_dir)
        assert os.path.isdir(new_dir)
    
    def test_create_nested_directories(self):
        """Test ensure_directory_exists with nested directory paths."""
        # Create a deeply nested path
        nested_file_path = os.path.join(self.nested_dir_path, "test.txt")
        
        # Ensure directories don't exist before test
        assert not os.path.exists(self.nested_dir_path)
        
        ensure_directory_exists(nested_file_path)
        
        # Directory structure should now exist
        assert os.path.exists(self.nested_dir_path)
        assert os.path.isdir(self.nested_dir_path)
    
    def test_existing_directory(self):
        """Test ensure_directory_exists with an existing directory."""
        # Create a directory
        exist_dir = os.path.join(self.temp_dir, "exist_dir")
        os.makedirs(exist_dir)
        
        # This should not raise an error
        ensure_directory_exists(os.path.join(exist_dir, "test.txt"))
        
        # Directory should still exist
        assert os.path.exists(exist_dir)
        assert os.path.isdir(exist_dir)
    
    def test_with_file_path_only(self):
        """Test ensure_directory_exists with just a filename (no directory)."""
        # This should not create any new directories
        ensure_directory_exists("just_filename.txt")
        
        # No new directories should be created in the current path
        assert not os.path.exists("just_filename")


class TestReadJsonFile(TestFileManipulation):
    """Tests for the read_json_file function."""
    
    @pytest.fixture(autouse=True)
    def setup_json_files(self, setup_teardown):
        """Set up JSON files for testing."""
        self.valid_json_path = os.path.join(self.temp_dir, "valid.json")
        self.valid_json_data = {"key": "value", "number": 123, "list": [1, 2, 3]}
        with open(self.valid_json_path, 'w') as f:
            json.dump(self.valid_json_data, f)
            
        self.invalid_json_path = os.path.join(self.temp_dir, "invalid.json")
        with open(self.invalid_json_path, 'w') as f:
            f.write("this is not json{")
            
        self.empty_json_path = os.path.join(self.temp_dir, "empty.json")
        with open(self.empty_json_path, 'w') as f:
            f.write("") # Empty file

    def test_read_valid_json(self):
        """Test reading a valid JSON file."""
        data = read_json_file(self.valid_json_path)
        assert data == self.valid_json_data
        
    def test_read_nonexistent_json(self):
        """Test reading a nonexistent JSON file raises FileNotFoundError."""
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent.json")
        with pytest.raises(FileNotFoundError):
            read_json_file(nonexistent_path)
            
    def test_read_invalid_json(self):
        """Test reading an invalid JSON file raises JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            read_json_file(self.invalid_json_path)
            
    def test_read_empty_file_json(self):
        """Test reading an empty file raises JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            read_json_file(self.empty_json_path)
            
    def test_read_json_no_permission(self):
        """Test reading JSON file without permission raises PermissionError."""
        if os.name != "nt":
            os.chmod(self.valid_json_path, 0o000)
            try:
                with pytest.raises(PermissionError):
                    read_json_file(self.valid_json_path)
            finally:
                os.chmod(self.valid_json_path, 0o666)


class TestWriteJsonFile(TestFileManipulation):
    """Tests for the write_json_file function."""
    
    def test_write_valid_json(self):
        """Test writing valid data to a JSON file."""
        output_path = os.path.join(self.temp_dir, "output.json")
        data_to_write = {"name": "test", "value": 42, "items": ["a", "b"]}
        write_json_file(output_path, data_to_write)
        
        # Verify content
        with open(output_path, 'r') as f:
            read_data = json.load(f)
        assert read_data == data_to_write
        
    def test_write_json_creates_directory(self):
        """Test write_json_file creates parent directories if they don't exist."""
        nested_output_path = os.path.join(self.nested_dir_path, "nested_output.json")
        data_to_write = {"nested": True}
        write_json_file(nested_output_path, data_to_write)
        
        assert os.path.exists(nested_output_path)
        with open(nested_output_path, 'r') as f:
            read_data = json.load(f)
        assert read_data == data_to_write
        
    def test_write_json_overwrite(self):
        """Test writing JSON overwrites an existing file."""
        output_path = os.path.join(self.temp_dir, "overwrite.json")
        initial_data = {"initial": True}
        with open(output_path, 'w') as f:
            json.dump(initial_data, f)
            
        new_data = {"overwritten": True}
        write_json_file(output_path, new_data)
        
        with open(output_path, 'r') as f:
            read_data = json.load(f)
        assert read_data == new_data
        
    def test_write_json_no_indent(self):
        """Test writing JSON with no indentation (compact)."""
        output_path = os.path.join(self.temp_dir, "compact.json")
        data_to_write = {"a": 1, "b": 2}
        write_json_file(output_path, data_to_write, indent=None)
        
        with open(output_path, 'r') as f:
            content = f.read()
        # Expect compact JSON, no newlines or significant spaces
        assert content == '{"a": 1, "b": 2}'
        
    def test_write_json_non_serializable(self):
        """Test writing non-serializable data raises TypeError."""
        output_path = os.path.join(self.temp_dir, "non_serializable.json")
        non_serializable_data = {"set": {1, 2, 3}} # Sets are not JSON serializable by default
        with pytest.raises(TypeError):
            write_json_file(output_path, non_serializable_data)
            
    def test_write_json_no_permission(self):
        """Test writing JSON file without permission raises PermissionError."""
        if os.name != "nt":
            read_only_dir = os.path.join(self.temp_dir, "read_only_json_dir")
            os.makedirs(read_only_dir)
            os.chmod(read_only_dir, 0o500) # r-x
            output_path = os.path.join(read_only_dir, "cannot_write.json")
            data_to_write = {"data": "test"}
            
            try:
                with pytest.raises(PermissionError):
                    write_json_file(output_path, data_to_write)
            finally:
                os.chmod(read_only_dir, 0o755)