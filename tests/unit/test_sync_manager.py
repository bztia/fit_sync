"""
Unit tests for the SyncManager class.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from fit_sync.sync import SyncManager

@pytest.fixture
def mock_config():
    """Create a mock configuration dict."""
    return {
        'accounts': {
            'garmin_us': {
                'email': 'test.us@example.com',
                'password': 'password'
            },
            'garmin_cn': {
                'email': 'test.cn@example.com',
                'password': 'password'
            },
            'coros_cn': {
                'email': 'test.cn@example.com',
                'password': 'password'
            }
        },
        'sync_rules': [
            {
                'source': 'garmin_us',
                'destination': 'garmin_cn',
                'activity_types': ['running', 'cycling'],
                'start_date': '2023-01-01',
                'conflict_strategy': 'skip_existing'
            }
        ],
        'cache': {
            'max_age_days': 7,
            'directory': '/tmp/fit_sync_test_cache'
        }
    }

@pytest.fixture
def mock_platform_factory():
    """Mock the platform classes to return the same platform instance."""
    with patch('fit_sync.platforms.garmin.GarminUSPlatform') as garmin_us_mock, \
         patch('fit_sync.platforms.garmin.GarminCNPlatform') as garmin_cn_mock, \
         patch('fit_sync.platforms.coros.CorosCNPlatform') as coros_cn_mock:
        
        platform_mock = MagicMock()
        garmin_us_mock.return_value = platform_mock
        garmin_cn_mock.return_value = platform_mock
        coros_cn_mock.return_value = platform_mock
        
        yield platform_mock

class TestSyncManager:
    """Tests for the SyncManager class."""
    
    def test_init_platforms(self, mock_config):
        """Test platform initialization."""
        sync_manager = SyncManager(mock_config)
        
        # Should have initialized platforms defined in mock_config
        assert 'garmin_us' in sync_manager.platforms
        assert 'garmin_cn' in sync_manager.platforms
        assert 'coros_cn' in sync_manager.platforms
    
    def test_authenticate_all_success(self, mock_config):
        """Test successful authentication with all platforms."""
        sync_manager = SyncManager(mock_config)
        
        with patch.object(sync_manager.platforms['garmin_us'], 'authenticate', return_value=True):
            with patch.object(sync_manager.platforms['garmin_cn'], 'authenticate', return_value=True):
                with patch.object(sync_manager.platforms['coros_cn'], 'authenticate', return_value=True):
                    # All authentications successful
                    assert sync_manager.authenticate_all() is True
    
    def test_authenticate_all_partial_failure(self, mock_config):
        """Test authentication with some platform failures."""
        sync_manager = SyncManager(mock_config)
        
        with patch.object(sync_manager.platforms['garmin_us'], 'authenticate', return_value=True):
            with patch.object(sync_manager.platforms['garmin_cn'], 'authenticate', return_value=False):
                with patch.object(sync_manager.platforms['coros_cn'], 'authenticate', return_value=True):
                    # One authentication failed
                    assert sync_manager.authenticate_all() is False
    
    def test_download_activity_success(self, mock_config, mock_fit_file):
        """Test successful activity download."""
        sync_manager = SyncManager(mock_config)
        platform_id = 'garmin_us'
        activity_id = 'activity_1'
        
        # Set up mocks
        with patch.object(sync_manager.platforms[platform_id], 'authenticate', return_value=True):
            with patch.object(sync_manager.platforms[platform_id], 'download_activity', return_value=mock_fit_file):
                # Test download without output directory
                result = sync_manager.download_activity(platform_id, activity_id)
                assert result == mock_fit_file
    
    def test_download_activity_with_output_dir(self, mock_config, mock_fit_file, temp_cache_dir):
        """Test activity download with custom output directory."""
        sync_manager = SyncManager(mock_config)
        platform_id = 'garmin_us'
        activity_id = 'activity_1'
        output_dir = temp_cache_dir / "downloads"
        
        # Set up mocks
        with patch.object(sync_manager.platforms[platform_id], 'authenticate', return_value=True):
            with patch.object(sync_manager.platforms[platform_id], 'download_activity', return_value=mock_fit_file):
                with patch('shutil.copy') as mock_copy:
                    # Test download with output directory
                    result = sync_manager.download_activity(
                        platform_id, 
                        activity_id, 
                        output_dir=str(output_dir)
                    )
                    
                    # Should have copied the file
                    mock_copy.assert_called_once()
                    assert result is not None
    
    def test_download_activity_with_custom_filename(self, mock_config, mock_fit_file, temp_cache_dir):
        """Test activity download with custom filename."""
        sync_manager = SyncManager(mock_config)
        platform_id = 'garmin_us'
        activity_id = 'activity_1'
        output_dir = temp_cache_dir / "downloads"
        custom_filename = "custom_activity.fit"
        
        # Set up mocks
        with patch.object(sync_manager.platforms[platform_id], 'authenticate', return_value=True):
            with patch.object(sync_manager.platforms[platform_id], 'download_activity', return_value=mock_fit_file):
                with patch('shutil.copy') as mock_copy:
                    # Test download with output directory and custom filename
                    result = sync_manager.download_activity(
                        platform_id, 
                        activity_id, 
                        output_dir=str(output_dir),
                        output_filename=custom_filename
                    )
                    
                    # Should have copied the file with custom name
                    mock_copy.assert_called_once()
                    assert mock_copy.call_args[0][1].name == custom_filename
                    assert result is not None
    
    def test_download_activity_auth_failure(self, mock_config):
        """Test activity download with authentication failure."""
        sync_manager = SyncManager(mock_config)
        platform_id = 'garmin_us'
        activity_id = 'activity_1'
        
        # Set up mock for authentication failure
        with patch.object(sync_manager.platforms[platform_id], 'authenticate', return_value=False):
            result = sync_manager.download_activity(platform_id, activity_id)
            assert result is None
    
    def test_download_activity_invalid_platform(self, mock_config):
        """Test activity download with invalid platform."""
        sync_manager = SyncManager(mock_config)
        platform_id = 'non_existent_platform'
        activity_id = 'activity_1'
        
        result = sync_manager.download_activity(platform_id, activity_id)
        assert result is None
    
    def test_download_activity_download_failure(self, mock_config, mock_platform_factory):
        """Test downloading an activity that fails."""
        platform_mock = mock_platform_factory
        platform_mock.authenticate.return_value = True
        platform_mock.download_activity.return_value = None
        
        # Create sync manager with mocked platforms
        with patch('fit_sync.sync.GarminUSPlatform', return_value=platform_mock), \
             patch('fit_sync.sync.GarminCNPlatform', return_value=platform_mock), \
             patch('fit_sync.sync.CorosCNPlatform', return_value=platform_mock):
            
            sync_manager = SyncManager(mock_config)
            result = sync_manager.download_activity('garmin_us', 'activity_1')
        
        # Should return None on failure
        assert result is None
        
    def test_activities_caching(self, mock_config, mock_platform_factory):
        """Test that activities are properly cached."""
        # Setup platform mock
        platform_mock = mock_platform_factory
        platform_mock.authenticate.return_value = True
        
        # First call should retrieve from platform
        mock_activities = [{'id': 'test_1'}, {'id': 'test_2'}]
        platform_mock.list_activities.return_value = mock_activities
        
        # Create sync manager with mocked platforms
        with patch('fit_sync.sync.GarminUSPlatform', return_value=platform_mock), \
             patch('fit_sync.sync.GarminCNPlatform', return_value=platform_mock), \
             patch('fit_sync.sync.CorosCNPlatform', return_value=platform_mock):
            
            sync_manager = SyncManager(mock_config)
            result1 = sync_manager.get_activities('garmin_us', limit=10)
            
            # Verify platform call
            assert platform_mock.authenticate.call_count >= 1
            assert platform_mock.list_activities.call_count >= 1
            
            # Reset mock for next call
            platform_mock.authenticate.reset_mock()
            platform_mock.list_activities.reset_mock()
            
            # Second call should use cache
            result2 = sync_manager.get_activities('garmin_us', limit=10)
            
            # Verify platform not called again
            assert platform_mock.authenticate.call_count == 0
            assert platform_mock.list_activities.call_count == 0
            
            # Results should be the same
            assert result1 == result2
            assert result1 == mock_activities
        
    def test_activities_cache_expiry(self, mock_config, mock_platform_factory, monkeypatch):
        """Test that activities cache expires after the specified time."""
        import datetime
        
        # Setup platform mock
        platform_mock = mock_platform_factory
        platform_mock.authenticate.return_value = True
        
        # Setup time mocking
        current_time = datetime.datetime(2024, 1, 1, 12, 0, 0)
        future_time = datetime.datetime(2024, 1, 1, 12, 31, 0)  # 31 minutes later
        
        # Mock datetime.now
        class MockDatetime(datetime.datetime):
            @classmethod
            def now(cls):
                return current_time
        
        # Create sync manager with mocked platforms
        with patch('fit_sync.sync.GarminUSPlatform', return_value=platform_mock), \
             patch('fit_sync.sync.GarminCNPlatform', return_value=platform_mock), \
             patch('fit_sync.sync.CorosCNPlatform', return_value=platform_mock):
            
            # First call at current time
            monkeypatch.setattr(datetime, 'datetime', MockDatetime)
            platform_mock.list_activities.return_value = [{'id': 'test_1'}]
            
            sync_manager = SyncManager(mock_config)
            sync_manager.get_activities('garmin_us', limit=10)
            
            # Reset mock for next call
            platform_mock.authenticate.reset_mock()
            platform_mock.list_activities.reset_mock()
            
            # Change mock time to future time (after cache expiry)
            current_time = future_time
            
            # Different activities for second call
            platform_mock.list_activities.return_value = [{'id': 'test_2'}]
            
            # This call should not use cache since it's expired
            result = sync_manager.get_activities('garmin_us', limit=10)
            
            # Verify platform called again after cache expiry
            assert platform_mock.authenticate.call_count >= 1
            assert platform_mock.list_activities.call_count >= 1
            
            # Result should be the new value
            assert result == [{'id': 'test_2'}]
        
    def test_clear_activities_cache(self, mock_config, mock_platform_factory):
        """Test clearing the activities cache."""
        # Setup platform mock
        platform_mock = mock_platform_factory
        platform_mock.authenticate.return_value = True
        platform_mock.list_activities.return_value = [{'id': 'test_1'}]
        
        # Create sync manager with mocked platforms
        with patch('fit_sync.sync.GarminUSPlatform', return_value=platform_mock), \
             patch('fit_sync.sync.GarminCNPlatform', return_value=platform_mock), \
             patch('fit_sync.sync.CorosCNPlatform', return_value=platform_mock):
            
            sync_manager = SyncManager(mock_config)
            sync_manager.get_activities('garmin_us', limit=10)
            
            # Reset mocks
            platform_mock.authenticate.reset_mock()
            platform_mock.list_activities.reset_mock()
            
            # Clear cache
            sync_manager.clear_activities_cache()
            
            # Next call should not use cache
            sync_manager.get_activities('garmin_us', limit=10)
            
            # Verify platform called again
            assert platform_mock.authenticate.call_count >= 1
            assert platform_mock.list_activities.call_count >= 1 