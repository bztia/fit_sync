"""
Unit tests for Garmin platform implementation.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from fit_sync.platforms.garmin import GarminPlatform, GarminUSPlatform, GarminCNPlatform


class TestGarminPlatform:
    """Tests for the base GarminPlatform class."""

    def test_init(self, temp_cache_dir):
        """Test initialization of GarminPlatform."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = GarminPlatform(credentials, str(temp_cache_dir))
        
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
        platform = GarminPlatform(credentials, str(temp_cache_dir))
        
        with patch('fit_sync.platforms.garmin.logger') as mock_logger:
            result = platform.authenticate()
            mock_logger.info.assert_called_once()
            assert result is True

    def test_list_activities_no_filter(self, temp_cache_dir):
        """Test listing activities without filters."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = GarminPlatform(credentials, str(temp_cache_dir))
        
        activities = platform.list_activities(limit=3)
        
        assert len(activities) == 3
        for activity in activities:
            assert "id" in activity
            assert "startTime" in activity
            assert "activityType" in activity
            assert "duration" in activity
            assert "distance" in activity

    def test_list_activities_with_type_filter(self, temp_cache_dir):
        """Test listing activities with activity type filter."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = GarminPlatform(credentials, str(temp_cache_dir))
        
        activities = platform.list_activities(limit=10, activity_type="running")
        
        assert len(activities) > 0
        for activity in activities:
            assert activity["activityType"] == "running"

    def test_list_activities_with_date_filter(self, temp_cache_dir):
        """Test listing activities with date filters."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = GarminPlatform(credentials, str(temp_cache_dir))
        
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
        platform = GarminPlatform(credentials, str(temp_cache_dir))
        
        activity_id = "test_activity_123"
        fit_file = platform.download_activity(activity_id)
        
        assert fit_file is not None
        assert fit_file.exists()
        assert fit_file.name == f"{activity_id}.fit"
        
        # Check file content
        with open(fit_file, 'r') as f:
            content = f.read()
            assert f"Mock FIT file for activity {activity_id}" in content

    def test_upload_activity(self, temp_cache_dir):
        """Test uploading an activity."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = GarminPlatform(credentials, str(temp_cache_dir))
        
        # Create a test FIT file
        fit_file = temp_cache_dir / "test_upload.fit"
        with open(fit_file, 'w') as f:
            f.write("Test FIT file content")
        
        activity_id = platform.upload_activity(fit_file)
        
        assert activity_id is not None
        assert isinstance(activity_id, str)


class TestGarminUSPlatform:
    """Tests for the GarminUSPlatform class."""

    def test_init(self, temp_cache_dir):
        """Test initialization of GarminUSPlatform."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = GarminUSPlatform(credentials, str(temp_cache_dir))
        
        assert platform.email == "test@example.com"
        assert platform.password == "test_password"
        assert platform.cache_dir == temp_cache_dir
        assert platform.base_url == "https://connect.garmin.com"


class TestGarminCNPlatform:
    """Tests for the GarminCNPlatform class."""

    def test_init(self, temp_cache_dir):
        """Test initialization of GarminCNPlatform."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = GarminCNPlatform(credentials, str(temp_cache_dir))
        
        assert platform.email == "test@example.com"
        assert platform.password == "test_password"
        assert platform.cache_dir == temp_cache_dir
        assert platform.base_url == "https://connect.garmin.cn" 