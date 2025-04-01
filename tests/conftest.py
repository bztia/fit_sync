"""
Global pytest fixtures for fit_sync tests.
"""

import os
import json
import pytest
import tempfile
from pathlib import Path

@pytest.fixture
def mock_config():
    """Create a mock configuration dictionary."""
    return {
        "accounts": {
            "garmin_us": {
                "email": "test.us@example.com",
                "password": "test_password"
            },
            "garmin_cn": {
                "email": "test.cn@example.com",
                "password": "test_password"
            },
            "coros_cn": {
                "email": "test.coros@example.com",
                "password": "test_password"
            }
        },
        "sync_rules": [
            {
                "source": "garmin_us",
                "destination": "garmin_cn",
                "activity_types": ["running", "cycling"],
                "start_date": "2023-01-01",
                "conflict_strategy": "skip_existing"
            },
            {
                "source": "coros_cn",
                "destination": "garmin_cn",
                "activity_types": ["trail_running", "hiking"],
                "start_date": "2023-01-01",
                "conflict_strategy": "replace_existing"
            }
        ],
        "cache": {
            "max_age_days": 7,
            "directory": "~/.fit_sync/cache"
        }
    }

@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for test cache files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def mock_config_file(mock_config, temp_cache_dir):
    """Create a temporary config file with mock configuration."""
    # Update the cache directory to the temporary directory
    mock_config["cache"]["directory"] = str(temp_cache_dir)
    
    # Create a temporary config file
    config_file = temp_cache_dir / "config.json"
    with open(config_file, 'w') as f:
        json.dump(mock_config, f)
    
    yield config_file

@pytest.fixture
def mock_activity_data():
    """Create mock activity data for testing."""
    return [
        {
            "id": "activity_1",
            "startTime": "2023-04-01 08:00:00",
            "activityType": "running",
            "duration": "30:00",
            "distance": "5.0 km", 
            "elevationGain": "50 m",
            "avgHR": 150,
            "calories": 300
        },
        {
            "id": "activity_2",
            "startTime": "2023-04-03 09:00:00",
            "activityType": "cycling",
            "duration": "45:00",
            "distance": "15.0 km",
            "elevationGain": "100 m",
            "avgHR": 140,
            "calories": 400
        },
        {
            "id": "activity_3",
            "startTime": "2023-04-05 07:30:00",
            "activityType": "swimming",
            "duration": "25:00",
            "distance": "1.5 km",
            "elevationGain": "0 m",
            "avgHR": 130,
            "calories": 250
        }
    ]

@pytest.fixture
def mock_fit_file(temp_cache_dir):
    """Create a mock FIT file for testing."""
    fit_file = temp_cache_dir / "test_activity.fit"
    with open(fit_file, 'w') as f:
        f.write("Mock FIT file content for testing")
    
    yield fit_file 