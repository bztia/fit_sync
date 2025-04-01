"""
Integration tests for fit_sync.
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from fit_sync.sync import SyncManager
from fit_sync.platforms.garmin import GarminUSPlatform, GarminCNPlatform
from fit_sync.platforms.coros import CorosCNPlatform


class TestEndToEnd:
    """End-to-end tests for fit_sync."""

    def test_full_sync_process(self, mock_config, temp_cache_dir):
        """Test the complete synchronization process."""
        # Setup mock configuration
        mock_config["cache"]["directory"] = str(temp_cache_dir)
        
        # Initialize sync manager
        manager = SyncManager(mock_config)
        
        # Authenticate with all platforms
        auth_result = manager.authenticate_all()
        assert auth_result is True
        
        # Execute sync with dry run option
        sync_result = manager.sync(dry_run=True)
        
        # Validate that sync would have processed activities
        assert sync_result > 0
        
        # Verify cache files were created
        assert os.path.exists(temp_cache_dir)
        
        # Verify cache directory is not empty - should contain downloaded FIT files
        cache_contents = list(temp_cache_dir.glob("*.fit"))
        assert len(cache_contents) > 0

    def test_rule_based_sync(self, mock_config, temp_cache_dir):
        """Test sync based on configured rules."""
        # Setup configuration with specific rules
        mock_config["cache"]["directory"] = str(temp_cache_dir)
        mock_config["sync_rules"] = [
            {
                "source": "garmin_us",
                "destination": "garmin_cn",
                "activity_types": ["running"],  # Only running activities
                "start_date": "2023-01-01",
                "conflict_strategy": "skip_existing"
            }
        ]
        
        # Initialize sync manager
        manager = SyncManager(mock_config)
        
        # Run sync
        sync_result = manager.sync(dry_run=True)
        
        # Check that sync would have processed some activities
        assert sync_result > 0
        
        # Verify files in cache directory (should be mostly running activities)
        fit_files = list(temp_cache_dir.glob("*.fit"))
        assert len(fit_files) > 0

    def test_filtered_sync(self, mock_config, temp_cache_dir):
        """Test sync with command-line filters overriding config rules."""
        # Setup mock configuration
        mock_config["cache"]["directory"] = str(temp_cache_dir)
    
        # Initialize sync manager
        manager = SyncManager(mock_config)
        
        # Mock platform methods to return some trail_running activities
        mock_activities = [
            {"id": "activity_1", "activityType": "trail_running", "startTimeLocal": "2023-06-15T09:00:00"},
            {"id": "activity_2", "activityType": "trail_running", "startTimeLocal": "2023-07-20T10:30:00"},
            {"id": "activity_3", "activityType": "hiking", "startTimeLocal": "2023-05-01T08:15:00"}
        ]
        
        # Mock list_activities to return our mock data
        manager.platforms["coros_cn"].list_activities = MagicMock(return_value=mock_activities)
        manager.platforms["coros_cn"].download_activity = MagicMock(return_value="/tmp/mock_fit_file.fit")
        manager.platforms["garmin_cn"].upload_activity = MagicMock(return_value="new_activity_id")
    
        # Sync with specific filters
        sync_result = manager.sync(
            source="coros_cn",
            destination="garmin_cn",
            activity_types=["trail_running"],
            start_date="2023-01-01",
            end_date="2023-12-31",
            dry_run=True
        )
    
        # Verify sync would have processed activities
        assert sync_result > 0
        
        # Verify only trail_running activities were processed
        calls = manager.platforms["coros_cn"].download_activity.call_args_list
        assert len(calls) == 2  # Only the 2 trail_running activities 