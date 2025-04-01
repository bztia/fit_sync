"""
Core synchronization functionality for fit_sync.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import datetime

from .platforms.garmin import GarminUSPlatform, GarminCNPlatform
from .platforms.coros import CorosCNPlatform

logger = logging.getLogger(__name__)

class SyncManager:
    """Manages the synchronization between fitness platforms."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the sync manager.
        
        Args:
            config: Configuration dictionary from config.json
        """
        self.config = config
        self.cache_dir = Path(config.get('cache', {}).get('directory', '~/.fit_sync/cache')).expanduser()
        self.platforms = {}
        self._activities_cache = {}  # 活动列表缓存
        self._activities_cache_timestamp = {}  # 缓存时间戳
        
        # Initialize platforms
        self._init_platforms()
        
    def _init_platforms(self):
        """Initialize platform instances based on configuration."""
        accounts = self.config.get('accounts', {})
        
        if 'garmin_us' in accounts:
            self.platforms['garmin_us'] = GarminUSPlatform(
                accounts['garmin_us'],
                str(self.cache_dir)
            )
            
        if 'garmin_cn' in accounts:
            self.platforms['garmin_cn'] = GarminCNPlatform(
                accounts['garmin_cn'],
                str(self.cache_dir)
            )
            
        if 'coros_cn' in accounts:
            self.platforms['coros_cn'] = CorosCNPlatform(
                accounts['coros_cn'],
                str(self.cache_dir)
            )
    
    def authenticate_all(self) -> bool:
        """
        Authenticate with all configured platforms.
        
        Returns:
            True if all authentications were successful, False otherwise
        """
        success = True
        for platform_id, platform in self.platforms.items():
            logger.info(f"Authenticating with {platform_id}")
            if not platform.authenticate():
                logger.error(f"Authentication failed for {platform_id}")
                success = False
                
        return success
    
    def download_activity(self, 
                        platform_id: str, 
                        activity_id: str, 
                        output_dir: Optional[str] = None,
                        output_filename: Optional[str] = None) -> Optional[Path]:
        """
        Download an activity FIT file from a platform.
        
        Args:
            platform_id: ID of the platform to download from
            activity_id: ID of the activity to download
            output_dir: Directory to save the downloaded file (optional)
            output_filename: Custom filename for the saved file (optional)
            
        Returns:
            Path to the downloaded file, or None if download failed
        """
        if platform_id not in self.platforms:
            logger.error(f"Platform {platform_id} not configured")
            return None
            
        platform = self.platforms[platform_id]
        
        # Authenticate before download
        if not platform.authenticate():
            logger.error(f"Authentication failed for {platform_id}")
            return None
            
        # Download the file
        fit_file = platform.download_activity(activity_id)
        if not fit_file:
            logger.error(f"Failed to download activity {activity_id}")
            return None
            
        # If output directory specified, copy the file there with custom name
        if output_dir:
            output_path = Path(output_dir)
            os.makedirs(output_path, exist_ok=True)
            
            # Use custom filename if provided, otherwise use original filename
            if output_filename:
                dest_file = output_path / output_filename
            else:
                dest_file = output_path / fit_file.name
                
            # Copy file
            import shutil
            shutil.copy(fit_file, dest_file)
            return dest_file
            
        return fit_file
        
    def sync(self, source=None, destination=None, activity_types=None, 
             start_date=None, end_date=None, dry_run=False, conflict_strategy=None):
        """
        Sync activities between platforms based on rules.
        
        Args:
            source (str, optional): Source platform ID. Overrides sync rules.
            destination (str, optional): Destination platform ID. Overrides sync rules.
            activity_types (list, optional): Activity types to sync. Overrides sync rules.
            start_date (str, optional): Start date for activities to sync (ISO format). Overrides sync rules.
            end_date (str, optional): End date for activities to sync (ISO format). Overrides sync rules.
            dry_run (bool): If True, don't actually upload activities, just simulate.
            conflict_strategy (str, optional): Strategy for handling conflicts (skip_existing or replace_existing).
                                              Overrides sync rules.
        
        Returns:
            int: Total number of activities synced.
        """
        rules = []
        configured_accounts = self.config.get("accounts", {}).keys()
        
        # If specific source/destination provided, create a single rule
        if source and destination:
            # Check if both platforms are configured
            if source not in configured_accounts:
                logging.error(f"Source platform {source} not configured")
                return 0
            if destination not in configured_accounts:
                logging.error(f"Destination platform {destination} not configured")
                return 0
            
            # Check if both platforms are in self.platforms
            if source not in self.platforms:
                logging.error(f"Source platform {source} not initialized")
                return 0
            if destination not in self.platforms:
                logging.error(f"Destination platform {destination} not initialized")
                return 0
            
            rules.append({
                "source": source,
                "destination": destination,
                "activity_types": activity_types,
                "start_date": start_date,
                "end_date": end_date,
                "conflict_strategy": conflict_strategy or "skip_existing"
            })
        else:
            # Otherwise, use rules from config
            for rule in self.config.get("sync_rules", []):
                source_id = rule.get("source")
                dest_id = rule.get("destination")
                
                # Skip rule if either platform not configured
                if source_id not in configured_accounts:
                    logging.error(f"Source platform {source_id} not configured")
                    continue
                if dest_id not in configured_accounts:
                    logging.error(f"Destination platform {dest_id} not configured")
                    continue
                
                # Skip rule if either platform not in self.platforms
                if source_id not in self.platforms:
                    logging.error(f"Source platform {source_id} not initialized")
                    continue
                if dest_id not in self.platforms:
                    logging.error(f"Destination platform {dest_id} not initialized")
                    continue
                
                rules.append(rule)
        
        total_synced = 0
        
        for rule in rules:
            source_id = rule.get("source")
            dest_id = rule.get("destination")
            
            # Apply filters from rule or parameters
            rule_activity_types = rule.get('activity_types', [])
            rule_start_date = start_date or rule.get('start_date')
            rule_end_date = end_date or rule.get('end_date')
            
            # List activities from source
            activities = self.platforms[source_id].list_activities(
                limit=100,  # Use a reasonable limit for batch processing
                activity_type=','.join(rule_activity_types) if rule_activity_types else None,
                start_date=rule_start_date,
                end_date=rule_end_date
            )
            
            # Filter activities based on activity type if needed
            if rule_activity_types:
                filtered_activities = [
                    activity for activity in activities 
                    if activity.get("activityType") in rule_activity_types
                ]
                logger.info(f"Filtered from {len(activities)} to {len(filtered_activities)} activities based on activity types")
                activities = filtered_activities
            
            logger.info(f"Found {len(activities)} activities to sync from {source_id} to {dest_id}")
            
            # Process activities
            for activity in activities:
                activity_id = activity.get('id')
                if not activity_id:
                    continue
                    
                # Download FIT file
                fit_file = self.platforms[source_id].download_activity(activity_id)
                if not fit_file:
                    logger.warning(f"Failed to download activity {activity_id}")
                    continue
                    
                if dry_run:
                    logger.info(f"[DRY RUN] Would upload {fit_file} to {dest_id}")
                    total_synced += 1
                    continue
                    
                # Upload to destination
                new_activity_id = self.platforms[dest_id].upload_activity(fit_file)
                if new_activity_id:
                    logger.info(f"Successfully synced activity {activity_id} to {dest_id} as {new_activity_id}")
                    total_synced += 1
                else:
                    logger.error(f"Failed to upload activity {activity_id} to {dest_id}")
                    
        return total_synced 

    def get_activities(self, 
                      platform_id: str,
                      limit: int = 10,
                      activity_type: Optional[str] = None,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      use_cache: bool = True,
                      cache_max_age: int = 30) -> List[Dict]:
        """
        Get activities from a platform with caching support.
        
        Args:
            platform_id: Platform ID to get activities from
            limit: Maximum number of activities to return
            activity_type: Filter by activity type
            start_date: Only include activities on or after this date (YYYY-MM-DD)
            end_date: Only include activities on or before this date (YYYY-MM-DD)
            use_cache: Whether to use cached results if available
            cache_max_age: Maximum age of cache in minutes (default: 30)
            
        Returns:
            List of activity dictionaries
        """
        if platform_id not in self.platforms:
            logger.error(f"Platform {platform_id} not configured")
            return []
            
        # Create cache key based on query parameters
        cache_key = f"{platform_id}:{limit}:{activity_type}:{start_date}:{end_date}"
        
        # Check if we have cached results that aren't expired
        current_time = datetime.datetime.now()
        if (use_cache and 
            cache_key in self._activities_cache and 
            cache_key in self._activities_cache_timestamp):
            
            cache_time = self._activities_cache_timestamp[cache_key]
            age_minutes = (current_time - cache_time).total_seconds() / 60
            
            if age_minutes <= cache_max_age:
                logger.debug(f"Using cached activities for {platform_id} (age: {age_minutes:.1f} minutes)")
                return self._activities_cache[cache_key]
            else:
                logger.debug(f"Cache expired for {platform_id} (age: {age_minutes:.1f} minutes)")
        
        # Authenticate with platform
        platform = self.platforms[platform_id]
        if not platform.authenticate():
            logger.error(f"Authentication failed for {platform_id}")
            return []
        
        # Get activities from platform
        activities = platform.list_activities(
            limit=limit,
            activity_type=activity_type,
            start_date=start_date,
            end_date=end_date
        )
        
        # Cache the results with timestamp
        self._activities_cache[cache_key] = activities
        self._activities_cache_timestamp[cache_key] = current_time
        logger.debug(f"Cached {len(activities)} activities for {platform_id}")
        
        return activities
        
    def clear_activities_cache(self):
        """Clear the activities cache."""
        self._activities_cache = {}
        self._activities_cache_timestamp = {}
        logger.debug("Activities cache cleared") 