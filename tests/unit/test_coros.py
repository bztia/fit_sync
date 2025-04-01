"""
Unit tests for Coros platform implementation.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from fit_sync.platforms.coros import CorosPlatform, CorosCNPlatform


class TestCorosPlatform:
    """Tests for the base CorosPlatform class."""

    def test_init(self, temp_cache_dir):
        """Test initialization of CorosPlatform."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = CorosPlatform(credentials, str(temp_cache_dir))
        
        assert platform.email == "test@example.com"
        assert platform.password == "test_password"
        assert platform.cache_dir == temp_cache_dir
        assert platform.session is None
        assert os.path.exists(temp_cache_dir)

    def test_authenticate(self, temp_cache_dir):
        """Test authenticate method."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = CorosPlatform(credentials, str(temp_cache_dir))
        
        with patch('fit_sync.platforms.coros.logger') as mock_logger:
            result = platform.authenticate()
            mock_logger.info.assert_called_once()
            assert result is True

    def test_list_activities_no_filter(self, temp_cache_dir):
        """Test listing activities without filters."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = CorosPlatform(credentials, str(temp_cache_dir))
        
        activities = platform.list_activities(limit=3)
        
        assert len(activities) == 3
        for activity in activities:
            assert "id" in activity
            assert "startTime" in activity
            assert "activityType" in activity
            assert "duration" in activity
            assert "distance" in activity
            # Check that IDs have the COROS prefix
            assert activity["id"].startswith("COROS_")

    def test_list_activities_with_type_filter(self, temp_cache_dir):
        """Test listing activities with activity type filter."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = CorosPlatform(credentials, str(temp_cache_dir))
        
        activities = platform.list_activities(limit=10, activity_type="trail_running")
        
        assert len(activities) > 0
        for activity in activities:
            assert activity["activityType"] == "trail_running"

    def test_list_activities_with_date_filter(self, temp_cache_dir):
        """Test listing activities with date filters."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = CorosPlatform(credentials, str(temp_cache_dir))
        
        # Get today's date and a future date
        import datetime
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        future = (datetime.datetime.now() + datetime.timedelta(days=10)).strftime("%Y-%m-%d")
        
        # No activities should be returned with a future date filter
        activities = platform.list_activities(limit=10, start_date=future)
        assert len(activities) == 0

    def test_download_activity(self, temp_cache_dir):
        """Test downloading an activity."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = CorosPlatform(credentials, str(temp_cache_dir))
        
        activity_id = "COROS_12345678"
        fit_file = platform.download_activity(activity_id)
        
        assert fit_file is not None
        assert fit_file.exists()
        assert fit_file.name == f"{activity_id}.fit"
        
        # Check file content
        with open(fit_file, 'r') as f:
            content = f.read()
            assert f"Mock COROS FIT file for activity {activity_id}" in content


class TestCorosCNPlatform:
    """Tests for the CorosCNPlatform class."""

    def test_init(self, temp_cache_dir):
        """Test initialization of CorosCNPlatform."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = CorosCNPlatform(credentials, str(temp_cache_dir))
        
        assert platform.email == "test@example.com"
        assert platform.password == "test_password"
        assert platform.cache_dir == temp_cache_dir
        assert platform.base_url == "https://api.coros.com"
        
    def test_coros_different_activity_types(self, temp_cache_dir):
        """Test that Coros uses different activity types than Garmin."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = CorosCNPlatform(credentials, str(temp_cache_dir))
        
        activities = platform.list_activities(limit=10)
        
        # Check that Coros-specific activity types are used
        found_types = set()
        for activity in activities:
            found_types.add(activity["activityType"])
        
        # Should find at least one Coros-specific activity type
        coros_types = ["trail_running", "mountaineering"]
        assert any(t in found_types for t in coros_types) 