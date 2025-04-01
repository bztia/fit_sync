"""
Unit tests for Coros platform implementation.
"""

import os
import pytest
import requests
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
        assert isinstance(platform.session, requests.Session)
        assert platform.token is None
        assert os.path.exists(temp_cache_dir)

    def test_authenticate(self, temp_cache_dir):
        """Test authenticate method."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = CorosPlatform(credentials, str(temp_cache_dir))
        
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 200,
            "data": {
                "token": "mock_token_123",
                "userId": "user_123",
                "email": "test@example.com"
            }
        }
        
        # Mock the token caching functions to avoid file operations
        with patch('fit_sync.platforms.coros.logger') as mock_logger, \
             patch('requests.Session.post', return_value=mock_response), \
             patch.object(platform, '_save_token_to_cache') as mock_save, \
             patch.object(platform, '_load_cached_token', return_value=False):
            
            # First call should authenticate via API
            result = platform.authenticate()
            
            mock_logger.info.assert_called()
            assert result is True
            assert platform.token == "mock_token_123"
            assert platform.user_id == "user_123"
            mock_save.assert_called_once()
            
        # Now test with cached token
        platform2 = CorosPlatform(credentials, str(temp_cache_dir))
        with patch('fit_sync.platforms.coros.logger') as mock_logger, \
             patch.object(platform2, '_load_cached_token', return_value=True) as mock_load:
            # Second call should use cached token
            result = platform2.authenticate()
            assert result is True
            mock_load.assert_called_once()
            mock_logger.info.assert_called()

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
        assert platform.base_url == "https://teamapi.coros.com"
        assert platform.web_url == "https://t.coros.com"
        assert platform.token_cache_file == platform.cache_dir / "coros_cn_token.json"
        
    def test_authenticate(self, temp_cache_dir):
        """Test CN platform authenticate method."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = CorosCNPlatform(credentials, str(temp_cache_dir))
        
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": "0000",
            "message": "OK",
            "data": {
                "accessToken": "mock_cn_token_123",
                "userId": "user_cn_123",
                "email": "test@example.com"
            }
        }
        
        # Mock the token caching functions to avoid file operations
        with patch('fit_sync.platforms.coros.logger') as mock_logger, \
             patch('requests.Session.post', return_value=mock_response), \
             patch.object(platform, '_save_token_to_cache') as mock_save, \
             patch.object(platform, '_load_cached_token', return_value=False):
            
            # First call should authenticate via API
            result = platform.authenticate()
            
            mock_logger.info.assert_called()
            assert result is True
            assert platform.token == "mock_cn_token_123"
            assert platform.user_id == "user_cn_123"
            mock_save.assert_called_once()
            
        # Now test with cached token
        platform2 = CorosCNPlatform(credentials, str(temp_cache_dir))
        with patch('fit_sync.platforms.coros.logger') as mock_logger, \
             patch.object(platform2, '_load_cached_token', return_value=True) as mock_load:
            # Second call should use cached token
            result = platform2.authenticate()
            assert result is True
            mock_load.assert_called_once()
            mock_logger.info.assert_called()
    
    def test_list_activities_cn(self, temp_cache_dir):
        """Test list_activities method for Coros CN platform."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = CorosCNPlatform(credentials, str(temp_cache_dir))
        platform.token = "mock_token_123"  # Set token directly to avoid authentication
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "apiCode": "C33BB719",
            "result": "0000",
            "message": "OK",
            "data": {
                "count": 1854,
                "dataList": [
                    {
                        "adjustedPace": 0,
                        "ascent": 3701,
                        "avgCadence": 90,
                        "avgHr": 104,
                        "avgPower": 139,
                        "avgSpeed": 816.81,
                        "calorie": 5818000,
                        "date": 20250323,
                        "descent": 3616,
                        "distance": 69282.4296875,
                        "endTime": 1742737890,
                        "labelId": "467870248094171141",
                        "mode": 15,
                        "sportType": 102,
                        "startTime": 1742680814,
                        "step": 98934,
                        "workoutTime": 56590
                    },
                    {
                        "adjustedPace": 0,
                        "ascent": 0,
                        "avgCadence": 166,
                        "avgHr": 109,
                        "avgPower": 325,
                        "avgSpeed": 357.23,
                        "calorie": 212000,
                        "date": 20250321,
                        "descent": 0,
                        "distance": 5050.0,
                        "endTime": 1742533550,
                        "labelId": "467870244870848516",
                        "mode": 8,
                        "sportType": 101,
                        "startTime": 1742531746,
                        "step": 5008,
                        "workoutTime": 1804
                    }
                ],
                "pageNumber": 1,
                "totalPage": 93
            }
        }
        
        # Mock get request
        with patch('fit_sync.platforms.coros.logger'), \
             patch('requests.Session.get', return_value=mock_response):
            
            # Test the list_activities method
            activities = platform.list_activities(limit=10)
            
            # Verify the results
            assert len(activities) == 2
            
            # Verify first activity
            assert activities[0]["id"] == "COROS_CN_467870248094171141"
            assert "trail_running" in activities[0]["activityType"]  # Sport type 102 should map to trail_running
            assert "69.28" in activities[0]["distance"]  # Distance should be in km
            assert activities[0]["avgHR"] == 104
            assert activities[0]["elevationGain"] == "3701 m"
            
            # Verify second activity
            assert activities[1]["id"] == "COROS_CN_467870244870848516"
            assert "treadmill" in activities[1]["activityType"]  # Sport type 101 should map to treadmill
            assert "5.05" in activities[1]["distance"]
    
    def test_download_activity_cn(self, temp_cache_dir):
        """Test downloading a FIT file from Coros CN platform."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = CorosCNPlatform(credentials, str(temp_cache_dir))
        platform.token = "mock_token_123"  # Set token directly to avoid authentication
        
        # Create mock binary content for FIT file
        mock_fit_content = b'\x0E\x10\x1C\xE82FIT\x00\x00\x00\x00\x00\x00\x00'
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [mock_fit_content]
        
        activity_id = "COROS_CN_467870248094171141"
        
        # Mock get request with context manager to ensure any file is cleaned up
        with patch('fit_sync.platforms.coros.logger'), \
             patch('requests.Session.get', return_value=mock_response):
            
            # Test the download_activity method
            fit_file = platform.download_activity(activity_id)
            
            # Verify the result
            assert fit_file is not None
            assert fit_file.exists()
            assert fit_file.name == f"{activity_id}.fit"
            
            # Verify file content (binary)
            with open(fit_file, 'rb') as f:
                content = f.read()
                assert content == mock_fit_content
        
    def test_coros_different_activity_types(self, temp_cache_dir):
        """Test that Coros uses different activity types than Garmin."""
        credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        platform = CorosCNPlatform(credentials, str(temp_cache_dir))
        platform.token = "mock_token_123"  # Set token directly to avoid authentication
        
        # Mock API response with specific activity types
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": "0000",
            "message": "OK",
            "data": {
                "count": 10,
                "dataList": [
                    {
                        "sportType": 102,  # trail_running
                        "startTime": 1742680814,
                        "distance": 10000.0,
                        "labelId": "123456789",
                        "workoutTime": 3600
                    },
                    {
                        "sportType": 111,  # mountaineering
                        "startTime": 1742531746,
                        "distance": 5000.0,
                        "labelId": "987654321",
                        "workoutTime": 1800
                    }
                ],
                "pageNumber": 1,
                "totalPage": 1
            }
        }
        
        # Mock get request
        with patch('fit_sync.platforms.coros.logger'), \
             patch('requests.Session.get', return_value=mock_response):
             
            activities = platform.list_activities(limit=10)
            
            # Check that Coros-specific activity types are used
            found_types = set()
            for activity in activities:
                found_types.add(activity["activityType"])
            
            # Should find at least one Coros-specific activity type
            coros_types = ["trail_running", "mountaineering"]
            assert any(t in found_types for t in coros_types) 