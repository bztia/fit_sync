"""
Unit tests for the SyncManager class.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from fit_sync.sync import SyncManager

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
    
    def test_download_activity_download_failure(self, mock_config):
        """Test activity download with download failure."""
        sync_manager = SyncManager(mock_config)
        platform_id = 'garmin_us'
        activity_id = 'activity_1'
        
        # Set up mocks
        with patch.object(sync_manager.platforms[platform_id], 'authenticate', return_value=True):
            with patch.object(sync_manager.platforms[platform_id], 'download_activity', return_value=None):
                result = sync_manager.download_activity(platform_id, activity_id)
                assert result is None 