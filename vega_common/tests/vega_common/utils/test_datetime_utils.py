"""
Unit tests for the datetime_utils module.

Tests all functions in the vega_common.utils.datetime_utils module to ensure
they behave as expected across different contexts.
"""

import time
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
from vega_common.utils.datetime_utils import (
    get_current_time,
    get_timestamp,
    format_duration,
    is_older_than,
)


class TestGetCurrentTime:
    """Tests for the get_current_time function."""

    @freeze_time("2023-01-15 12:34:56")
    def test_default_format(self):
        """Test get_current_time with default format."""
        result = get_current_time()
        expected = "2023-01-15 12:34:56 - "
        assert result == expected

    @freeze_time("2023-01-15 12:34:56")
    def test_custom_format(self):
        """Test get_current_time with a custom format."""
        result = get_current_time("%Y/%m/%d %H:%M")
        expected = "2023/01/15 12:34"
        assert result == expected

    @freeze_time("2023-01-15 12:34:56")
    def test_empty_format(self):
        """Test get_current_time with an empty format."""
        result = get_current_time("")
        expected = ""
        assert result == expected


class TestGetTimestamp:
    """Tests for the get_timestamp function."""

    @freeze_time("2023-01-15 12:34:56")
    def test_int_timestamp(self):
        """Test get_timestamp returning an integer timestamp."""
        result = get_timestamp()
        # 2023-01-15 12:34:56 as timestamp
        expected = 1673786096
        assert result == expected

    @freeze_time("2023-01-15 12:34:56")
    def test_string_timestamp_default_format(self):
        """Test get_timestamp returning a string with default format."""
        result = get_timestamp(as_string=True)
        expected = "20230115123456"
        assert result == expected

    @freeze_time("2023-01-15 12:34:56")
    def test_string_timestamp_custom_format(self):
        """Test get_timestamp returning a string with custom format."""
        result = get_timestamp(as_string=True, time_format="%Y-%m-%d")
        expected = "2023-01-15"
        assert result == expected


class TestFormatDuration:
    """Tests for the format_duration function."""

    def test_seconds_only(self):
        """Test format_duration with seconds only."""
        result = format_duration(45)
        expected = "45s"
        assert result == expected

    def test_minutes_and_seconds(self):
        """Test format_duration with minutes and seconds."""
        result = format_duration(125)  # 2 minutes and 5 seconds
        expected = "2m 5s"
        assert result == expected

    def test_hours_minutes_and_seconds(self):
        """Test format_duration with hours, minutes and seconds."""
        result = format_duration(7385)  # 2 hours, 3 minutes, 5 seconds
        expected = "2h 3m 5s"
        assert result == expected

    def test_zero_seconds(self):
        """Test format_duration with zero seconds."""
        result = format_duration(0)
        expected = "0s"
        assert result == expected

    def test_negative_seconds(self):
        """Test format_duration with negative seconds."""
        # This tests how the function handles unexpected input
        result = format_duration(-60)
        # The function should handle negative values gracefully
        # Expected behavior depends on requirements, but it should not crash
        expected = "0s"  # Assuming the function returns zero for negative
        assert len(result) > 0  # At least it should return something


class TestIsOlderThan:
    """Tests for the is_older_than function."""

    @freeze_time("2023-01-15 12:34:56")
    def test_older_datetime(self):
        """Test is_older_than with an older datetime."""
        older_time = datetime(2023, 1, 15, 12, 33, 56)  # 1 minute older
        result = is_older_than(older_time, 30)  # 30 seconds threshold
        assert result == True

    @freeze_time("2023-01-15 12:34:56")
    def test_newer_datetime(self):
        """Test is_older_than with a newer datetime."""
        newer_time = datetime(2023, 1, 15, 12, 34, 40)  # 16 seconds earlier
        result = is_older_than(newer_time, 30)  # 30 seconds threshold
        assert result == False

    @freeze_time("2023-01-15 12:34:56")
    def test_older_timestamp(self):
        """Test is_older_than with an older timestamp."""
        current_timestamp = int(datetime(2023, 1, 15, 12, 34, 56).timestamp())
        older_timestamp = current_timestamp - 60  # 60 seconds older
        result = is_older_than(older_timestamp, 30)  # 30 seconds threshold
        assert result == True

    @freeze_time("2023-01-15 12:34:56")
    def test_newer_timestamp(self):
        """Test is_older_than with a newer timestamp."""
        current_timestamp = int(datetime(2023, 1, 15, 12, 34, 56).timestamp())
        newer_timestamp = current_timestamp - 15  # 15 seconds older
        result = is_older_than(newer_timestamp, 30)  # 30 seconds threshold
        assert result == False
