"""
Unit tests for sync manager implementation.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from fit_sync.sync import SyncManager
from fit_sync.platforms.garmin import GarminUSPlatform, GarminCNPlatform
from fit_sync.platforms.coros import CorosCNPlatform


class TestSyncManager:
    """Tests for the SyncManager class."""

    def test_init(self, mock_config, temp_cache_dir):
        """Test initialization of SyncManager."""
        # Update cache directory in config
        mock_config["cache"]["directory"] = str(temp_cache_dir)
        
        manager = SyncManager(mock_config)
        
        assert manager.config == mock_config
        assert manager.cache_dir == temp_cache_dir
        assert isinstance(manager.platforms, dict)
        assert len(manager.platforms) == 3
        assert "garmin_us" in manager.platforms
        assert "garmin_cn" in manager.platforms
        assert "coros_cn" in manager.platforms
        assert isinstance(manager.platforms["garmin_us"], GarminUSPlatform)
        assert isinstance(manager.platforms["garmin_cn"], GarminCNPlatform)
        assert isinstance(manager.platforms["coros_cn"], CorosCNPlatform)

    def test_authenticate_all_success(self, mock_config, temp_cache_dir):
        """Test authenticate_all method when all authentications succeed."""
        mock_config["cache"]["directory"] = str(temp_cache_dir)
        manager = SyncManager(mock_config)
        
        # Mock all platform authenticate methods to return True
        for platform_id, platform in manager.platforms.items():
            platform.authenticate = MagicMock(return_value=True)
        
        result = manager.authenticate_all()
        
        assert result is True
        for platform_id, platform in manager.platforms.items():
            platform.authenticate.assert_called_once()

    def test_authenticate_all_some_failure(self, mock_config, temp_cache_dir):
        """Test authenticate_all method when some authentications fail."""
        mock_config["cache"]["directory"] = str(temp_cache_dir)
        manager = SyncManager(mock_config)
        
        # Mock platform authenticate methods with mixed results
        manager.platforms["garmin_us"].authenticate = MagicMock(return_value=True)
        manager.platforms["garmin_cn"].authenticate = MagicMock(return_value=False)
        manager.platforms["coros_cn"].authenticate = MagicMock(return_value=True)
        
        result = manager.authenticate_all()
        
        assert result is False
        manager.platforms["garmin_us"].authenticate.assert_called_once()
        manager.platforms["garmin_cn"].authenticate.assert_called_once()
        manager.platforms["coros_cn"].authenticate.assert_called_once()

    def test_sync_with_config_rules(self, mock_config, temp_cache_dir, mock_fit_file):
        """Test sync method using rules from config."""
        mock_config["cache"]["directory"] = str(temp_cache_dir)
        manager = SyncManager(mock_config)
        
        # Create mock activities for each platform
        garmin_us_activities = [
            {"id": "garmin_us_1", "activityType": "running"},
            {"id": "garmin_us_2", "activityType": "cycling"}
        ]
        coros_cn_activities = [
            {"id": "coros_cn_1", "activityType": "trail_running"},
            {"id": "coros_cn_2", "activityType": "hiking"}
        ]
        
        # Mock platform methods
        manager.platforms["garmin_us"].list_activities = MagicMock(return_value=garmin_us_activities)
        manager.platforms["garmin_us"].download_activity = MagicMock(return_value=mock_fit_file)
        
        manager.platforms["coros_cn"].list_activities = MagicMock(return_value=coros_cn_activities)
        manager.platforms["coros_cn"].download_activity = MagicMock(return_value=mock_fit_file)
        
        manager.platforms["garmin_cn"].upload_activity = MagicMock(return_value="new_activity_id")
        
        # Run sync
        result = manager.sync()
        
        # Expected to sync 4 activities (2 from garmin_us, 2 from coros_cn)
        assert result == 4
        
        # Check that list_activities was called for each source
        manager.platforms["garmin_us"].list_activities.assert_called_once()
        manager.platforms["coros_cn"].list_activities.assert_called_once()
        
        # Check that download_activity was called for each activity
        assert manager.platforms["garmin_us"].download_activity.call_count == 2
        assert manager.platforms["coros_cn"].download_activity.call_count == 2
        
        # Check that upload_activity was called for each activity
        assert manager.platforms["garmin_cn"].upload_activity.call_count == 4

    def test_sync_with_override_params(self, mock_config, temp_cache_dir, mock_fit_file):
        """Test sync method with overridden parameters."""
        mock_config["cache"]["directory"] = str(temp_cache_dir)
        manager = SyncManager(mock_config)
        
        # Create mock activities
        activities = [
            {"id": "test_1", "activityType": "running"},
            {"id": "test_2", "activityType": "cycling"}
        ]
        
        # Mock platform methods
        manager.platforms["garmin_us"].list_activities = MagicMock(return_value=activities)
        manager.platforms["garmin_us"].download_activity = MagicMock(return_value=mock_fit_file)
        manager.platforms["garmin_cn"].upload_activity = MagicMock(return_value="new_activity_id")
        
        # Run sync with overridden parameters
        result = manager.sync(
            source="garmin_us",
            destination="garmin_cn",
            activity_types=["running"],
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        
        # Should only sync activities from the specified source and with specified filters
        assert result == 1  # Only the running activity should be synced
        manager.platforms["garmin_us"].list_activities.assert_called_once()
        assert manager.platforms["garmin_us"].download_activity.call_count == 1
        manager.platforms["garmin_us"].download_activity.assert_called_with("test_1")
        assert manager.platforms["garmin_cn"].upload_activity.call_count == 1

    def test_sync_dry_run(self, mock_config, temp_cache_dir, mock_fit_file):
        """Test sync method in dry run mode."""
        mock_config["cache"]["directory"] = str(temp_cache_dir)
        manager = SyncManager(mock_config)
        
        # Create mock activities
        activities = [
            {"id": "test_1", "activityType": "running"},
            {"id": "test_2", "activityType": "cycling"}
        ]
        
        # Mock platform methods
        manager.platforms["garmin_us"].list_activities = MagicMock(return_value=activities)
        manager.platforms["garmin_us"].download_activity = MagicMock(return_value=mock_fit_file)
        manager.platforms["garmin_cn"].upload_activity = MagicMock(return_value="new_activity_id")
        
        # Run sync in dry run mode
        result = manager.sync(
            source="garmin_us",
            destination="garmin_cn",
            dry_run=True
        )
        
        # Should count the activities that would be synced, but not actually upload them
        assert result == 2
        manager.platforms["garmin_us"].list_activities.assert_called_once()
        assert manager.platforms["garmin_us"].download_activity.call_count == 2
        manager.platforms["garmin_cn"].upload_activity.assert_not_called()

    def test_sync_missing_platforms(self, mock_config, temp_cache_dir):
        """Test sync method with missing platforms."""
        mock_config["cache"]["directory"] = str(temp_cache_dir)
        # Remove one platform from config
        del mock_config["accounts"]["coros_cn"]
        
        manager = SyncManager(mock_config)
        
        # Mock platform methods to simulate activities
        activities = [{"id": f"activity_{i}", "activityType": "running"} for i in range(100)]
        manager.platforms["garmin_us"].list_activities = MagicMock(return_value=activities)
        manager.platforms["garmin_us"].download_activity = MagicMock(return_value="/tmp/mock_fit_file.fit")
        manager.platforms["garmin_cn"].upload_activity = MagicMock(return_value="new_activity_id")
        
        # Run sync
        result = manager.sync()
        
        # Should only execute rules with configured platforms (garmin_us -> garmin_cn)
        # and skip rules with missing platforms (coros_cn -> garmin_cn)
        assert result > 0  # Should sync from garmin_us to garmin_cn
        
        # Verify the correct platforms were called
        manager.platforms["garmin_us"].list_activities.assert_called_once()
        assert manager.platforms["garmin_us"].download_activity.call_count > 0
        assert manager.platforms["garmin_cn"].upload_activity.call_count > 0 