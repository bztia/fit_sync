"""
Coros platform implementation for fit_sync.
"""

import logging
import os
import datetime
import uuid
import hashlib
import requests
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import timedelta

logger = logging.getLogger(__name__)

class CorosPlatform:
    """Base class for Coros platform implementations."""
    
    def __init__(self, credentials: Dict[str, str], cache_dir: str):
        """
        Initialize the Coros platform.
        
        Args:
            credentials: Dictionary containing 'email' and 'password'
            cache_dir: Directory to store cached data
        """
        self.email = credentials.get('email')
        self.password = credentials.get('password')
        self.cache_dir = Path(cache_dir)
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.base_url = "https://api.coros.com"
        self.web_url = "https://www.coros.com"
        self.token_cache_file = self.cache_dir / "coros_token.json"
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_cached_token(self) -> bool:
        """
        Load token from the cache file if it exists and is not expired.
        
        Returns:
            True if a valid token was loaded, False otherwise
        """
        if not self.token_cache_file.exists():
            return False
        
        try:
            with open(self.token_cache_file, 'r') as f:
                cache_data = json.load(f)
                
            # Check if token is for current user
            if cache_data.get('email') != self.email:
                return False
                
            # Check if token is expired
            expiry_time = datetime.fromisoformat(cache_data.get('expiry_time', '2000-01-01T00:00:00'))
            if datetime.now() > expiry_time:
                logger.debug("Cached token has expired")
                return False
                
            # Load token and user_id
            self.token = cache_data.get('token')
            self.user_id = cache_data.get('user_id')
            
            if self.token:
                # Update session headers with token
                self.session.headers.update({
                    'Authorization': f"Bearer {self.token}"
                })
                logger.info(f"Using cached token for {self.email}")
                return True
                
        except Exception as e:
            logger.debug(f"Error loading cached token: {str(e)}")
            
        return False
        
    def _save_token_to_cache(self, token_data: Dict[str, Any]):
        """
        Save token and user info to cache file.
        
        Args:
            token_data: Dictionary containing token and user info
        """
        try:
            # Set token expiry to 12 hours from now (conservative estimate)
            cache_data = {
                'email': self.email,
                'token': self.token,
                'user_id': self.user_id,
                'expiry_time': (datetime.now() + timedelta(hours=12)).isoformat(),
                'platform': self.__class__.__name__
            }
            
            with open(self.token_cache_file, 'w') as f:
                json.dump(cache_data, f)
                
            logger.debug(f"Saved token to cache for {self.email}")
            
        except Exception as e:
            logger.debug(f"Error saving token to cache: {str(e)}")
    
    def authenticate(self) -> bool:
        """
        Authenticate with the Coros platform.
        
        Returns:
            True if authentication was successful, False otherwise
        """
        logger.info(f"Authenticating with Coros as {self.email}")
        
        # Try to load token from cache first
        if self._load_cached_token():
            return True
            
        if not self.email or not self.password:
            logger.error("Email or password missing")
            return False
        
        # Prepare headers
        headers = {
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'origin': self.web_url,
            'referer': self.web_url + '/',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        }
        
        # Prepare login data
        login_data = {
            "account": self.email,
            "accountType": 2,  # Email login type
            "pwd": hashlib.md5(self.password.encode()).hexdigest()
        }
        
        try:
            # Make login request
            login_url = f"{self.base_url}/account/login"
            logger.debug(f"Sending login request to {login_url}")
            response = self.session.post(
                login_url,
                headers=headers,
                json=login_data
            )
            
            # Check response
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get('code') == 200:
                    # Extract and store auth token
                    self.token = response_data.get('data', {}).get('token')
                    if self.token:
                        logger.info("Coros authentication successful")
                        
                        # Update session headers with token for subsequent requests
                        self.session.headers.update({
                            'Authorization': f"Bearer {self.token}"
                        })
                        
                        # Get user ID if available
                        self.user_id = response_data.get('data', {}).get('userId')
                        
                        # Save token to cache
                        self._save_token_to_cache(response_data.get('data', {}))
                        
                        return True
                    else:
                        logger.error("Authentication successful but no token received")
                else:
                    error_msg = response_data.get('msg', 'Unknown error')
                    logger.error(f"Authentication failed: {error_msg}")
            else:
                logger.error(f"Authentication failed with status code: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            
        return False
        
    def list_activities(self, 
                        limit: int = 10, 
                        activity_type: Optional[str] = None,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> List[Dict]:
        """
        List activities from the Coros platform.
        
        Args:
            limit: Maximum number of activities to return
            activity_type: Filter by activity type
            start_date: Only include activities on or after this date (YYYY-MM-DD)
            end_date: Only include activities on or before this date (YYYY-MM-DD)
            
        Returns:
            List of activity dictionaries
        """
        logger.info(f"Listing up to {limit} activities from Coros")
        
        # Generate sample data for stub implementation
        activities = []
        # Coros activity types are different from Garmin
        activity_types = ["trail_running", "hiking", "mountaineering", "indoor_run"]
        
        # Apply activity_type filter if specified
        if activity_type:
            filtered_types = activity_type.split(',')
            activity_types = [t for t in activity_types if t in filtered_types]
            
        # Create sample activities
        for i in range(limit):
            # Generate a date between 2023-01-01 and today
            days_ago = i * 3  # Every 3 days to make it different from Garmin
            activity_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
            activity_date_str = activity_date.strftime("%Y-%m-%d %H:%M:%S")
            
            # Check date filters
            if start_date and activity_date.strftime("%Y-%m-%d") < start_date:
                continue
                
            if end_date and activity_date.strftime("%Y-%m-%d") > end_date:
                continue
            
            activity = {
                "id": f"COROS_{uuid.uuid4().hex[:8]}",  # Make Coros IDs distinct
                "startTime": activity_date_str,
                "activityType": activity_types[i % len(activity_types)],
                "duration": f"00:{45 + i * 3:02d}:{i*2:02d}",  # Format as HH:MM:SS
                "distance": f"{8.0 + i * 0.8:.1f} km",
                "elevationGain": f"{i * 25} m",
                "avgHR": 145 + i,
                "calories": 300 + i * 60
            }
            activities.append(activity)
        
        return activities
        
    def download_activity(self, activity_id: str) -> Optional[Path]:
        """
        Download a FIT file for an activity.
        
        Args:
            activity_id: The Coros activity ID
            
        Returns:
            Path to the downloaded FIT file, or None if download failed
        """
        logger.info(f"Downloading activity {activity_id} from Coros")
        
        # Create a mock file in the cache directory
        fit_file = self.cache_dir / f"{activity_id}.fit"
        
        # Create an empty file
        with open(fit_file, 'w') as f:
            f.write(f"Mock COROS FIT file for activity {activity_id}")
            
        return fit_file


class CorosCNPlatform(CorosPlatform):
    """Coros China platform implementation."""
    
    def __init__(self, credentials: Dict[str, str], cache_dir: str):
        super().__init__(credentials, cache_dir)
        self.base_url = "https://teamapi.coros.com"
        self.web_url = "https://t.coros.com"
        self.token_cache_file = self.cache_dir / "coros_cn_token.json"
    
    def _hash_password(self, password: str) -> str:
        """
        Hash the password with MD5 for COROS CN login.
        
        Args:
            password: Plain text password
            
        Returns:
            MD5 hashed password
        """
        return hashlib.md5(password.encode()).hexdigest()
    
    def authenticate(self) -> bool:
        """
        Authenticate with the COROS CN platform.
        
        Returns:
            True if authentication was successful, False otherwise
        """
        logger.info(f"Authenticating with Coros CN as {self.email}")
        
        # Try to load token from cache first
        if self._load_cached_token():
            return True
        
        if not self.email or not self.password:
            logger.error("Email or password missing")
            return False
        
        # Prepare headers
        headers = {
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'origin': self.web_url,
            'referer': self.web_url + '/',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        }
        
        # Prepare login data
        login_data = {
            "account": self.email,
            "accountType": 2,  # Email login type
            "pwd": self._hash_password(self.password)
        }
        
        try:
            # Make login request
            login_url = f"{self.base_url}/account/login"
            logger.debug(f"Sending login request to {login_url}")
            response = self.session.post(
                login_url,
                headers=headers,
                json=login_data
            )
            
            # Check response
            if response.status_code == 200:
                response_data = response.json()
                logger.debug(f"Response data: {json.dumps(response_data)}")
                
                # COROS API uses "result" field with "0000" for success
                if response_data.get('result') == "0000" and response_data.get('message') == "OK":
                    # Extract and store auth token
                    access_token = response_data.get('data', {}).get('accessToken')
                    if access_token:
                        self.token = access_token
                        logger.info("COROS CN authentication successful")
                        
                        # Update session headers with token for subsequent requests
                        self.session.headers.update({
                            'accesstoken': self.token
                        })
                        
                        # Store the user ID for later use
                        self.user_id = response_data.get('data', {}).get('userId')
                        
                        # Save token to cache
                        self._save_token_to_cache(response_data.get('data', {}))
                        
                        return True
                    else:
                        logger.error("Authentication successful but no access token received")
                else:
                    # Log more detailed error message
                    api_code = response_data.get('apiCode')
                    result_code = response_data.get('result')
                    error_msg = response_data.get('message', 'Unknown error')
                    logger.error(f"Authentication failed with result '{result_code}', apiCode '{api_code}': {error_msg}")
            else:
                logger.error(f"Authentication failed with status code: {response.status_code}")
                try:
                    error_content = response.text
                    logger.error(f"Error response: {error_content}")
                except:
                    pass
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
        return False
        
    def list_activities(self, 
                        limit: int = 20, 
                        activity_type: Optional[str] = None,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> List[Dict]:
        """
        List activities from the Coros CN platform using the real API.
        
        Args:
            limit: Maximum number of activities to return
            activity_type: Filter by activity type
            start_date: Only include activities on or after this date (YYYY-MM-DD)
            end_date: Only include activities on or before this date (YYYY-MM-DD)
            
        Returns:
            List of activity dictionaries
        """
        logger.info(f"Listing up to {limit} activities from Coros CN")
        
        if not self.token:
            if not self.authenticate():
                logger.error("Failed to authenticate with Coros CN")
                return []
        
        # Set cookies with the token
        cookies = {
            'CPL-coros-region': '2',  # China region
            'CPL-coros-token': self.token
        }
        
        # Prepare parameters for activity list query
        page_size = min(limit, 20)  # API default is 20 per page
        page_number = 1
        
        # Prepare activity type filter if specified
        mode_list = ''
        if activity_type:
            # Map activity types to Coros codes if needed
            # This would need to be expanded based on Coros activity type codes
            activity_map = {
                'running': '8',
                'cycling': '15',
                'swimming': '19',
                'trail_running': '8',
                'hiking': '15'
            }
            modes = []
            for act_type in activity_type.split(','):
                if act_type in activity_map:
                    modes.append(activity_map[act_type])
            if modes:
                mode_list = ','.join(modes)
        
        # Build query URL with parameters
        query_url = f"https://teamcnapi.coros.com/activity/query?size={page_size}&pageNumber={page_number}&modeList={mode_list}"
        
        # Add date filters if specified
        date_params = {}
        if start_date:
            # Convert YYYY-MM-DD to Coros date format (YYYYMMDD)
            start_date_formatted = start_date.replace('-', '')
            date_params['startDate'] = start_date_formatted
            
        if end_date:
            # Convert YYYY-MM-DD to Coros date format (YYYYMMDD)
            end_date_formatted = end_date.replace('-', '')
            date_params['endDate'] = end_date_formatted
            
        # Update query URL with date parameters if any
        if date_params:
            for key, value in date_params.items():
                query_url += f"&{key}={value}"
        
        # Make the request to get activities
        logger.debug(f"Sending activity list request to {query_url}")
        try:
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accesstoken': self.token,
                'origin': 'https://trainingcn.coros.com',
                'referer': 'https://trainingcn.coros.com/',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
            }
            
            response = self.session.get(
                query_url,
                headers=headers,
                cookies=cookies
            )
            
            # Check response
            if response.status_code == 200:
                response_data = response.json()
                
                # Check if the request was successful
                if response_data.get('result') == "0000" and response_data.get('message') == "OK":
                    activities_data = response_data.get('data', {}).get('dataList', [])
                    logger.info(f"Got {len(activities_data)} activities from Coros CN")
                    
                    # Convert to standardized format
                    formatted_activities = []
                    for activity in activities_data:
                        # Get activity date and time
                        start_time = activity.get('startTime')
                        activity_date = datetime.datetime.fromtimestamp(start_time)
                        
                        # Map activity types
                        sport_type = activity.get('sportType')
                        activity_type_map = {
                            100: 'running',
                            101: 'treadmill',
                            102: 'trail_running',
                            103: 'track_running',
                            108: 'indoor_walk',
                            109: 'walk',
                            110: 'hike',
                            115: 'cycling',
                            119: 'swimming',
                            111: 'mountaineering',
                            # Add more mappings as needed
                        }
                        
                        mapped_activity_type = activity_type_map.get(sport_type, 'other')
                        
                        # Calculate duration in minutes:seconds
                        duration_seconds = activity.get('workoutTime', 0)
                        hours = duration_seconds // 3600
                        minutes = (duration_seconds % 3600) // 60
                        seconds = duration_seconds % 60
                        duration_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        
                        # Format distance in km
                        distance_meters = activity.get('distance', 0)
                        distance_km = distance_meters / 1000.0
                        
                        # Create formatted activity
                        formatted_activity = {
                            "id": f"COROS_CN_{activity.get('labelId')}",
                            "startTime": activity_date.strftime("%Y-%m-%d %H:%M:%S"),
                            "activityType": mapped_activity_type,
                            "duration": duration_formatted,
                            "distance": f"{distance_km:.2f} km",
                            "elevationGain": f"{activity.get('ascent', 0)} m",
                            "avgHR": activity.get('avgHr', 0),
                            "calories": activity.get('calorie', 0) / 1000  # Convert milliCalories to calories
                        }
                        
                        formatted_activities.append(formatted_activity)
                    
                    return formatted_activities
                else:
                    logger.error(f"Failed to get activities: {response_data.get('message')}")
            else:
                logger.error(f"Failed to get activities with status code: {response.status_code}")
                try:
                    logger.error(f"Error response: {response.text}")
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error fetching activities: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        return []
        
    def download_activity(self, activity_id: str) -> Optional[Path]:
        """
        Download a FIT file for an activity from Coros CN platform.
        
        Args:
            activity_id: The Coros activity ID (format: COROS_CN_{activity_id})
            
        Returns:
            Path to the downloaded FIT file, or None if download failed
        """
        logger.info(f"Downloading activity {activity_id} from Coros CN")
        
        if not self.token:
            if not self.authenticate():
                logger.error("Failed to authenticate with Coros CN")
                return None
        
        # Extract the actual activity ID from the formatted ID
        # Format is COROS_CN_{activity_id}
        if activity_id.startswith("COROS_CN_"):
            coros_activity_id = activity_id[9:]  # Remove the "COROS_CN_" prefix
        else:
            coros_activity_id = activity_id  # Use as is if no prefix
            
        logger.debug(f"Extracted Coros activity ID: {coros_activity_id}")
        
        # Set cookies with the token
        cookies = {
            'CPL-coros-region': '2',  # China region
            'CPL-coros-token': self.token
        }
        
        # Build download URL
        download_url = f"https://teamcnapi.coros.com/activity/export/fit/{coros_activity_id}"
        
        # Make the request to download the FIT file
        logger.debug(f"Sending FIT file download request to {download_url}")
        try:
            headers = {
                'accept': 'application/octet-stream',
                'accesstoken': self.token,
                'origin': 'https://trainingcn.coros.com',
                'referer': 'https://trainingcn.coros.com/',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
            }
            
            response = self.session.get(
                download_url,
                headers=headers,
                cookies=cookies,
                stream=True  # Use streaming for binary files
            )
            
            # Check response
            if response.status_code == 200:
                # Prepare output file path
                fit_file = self.cache_dir / f"{activity_id}.fit"
                
                # Save the downloaded file
                with open(fit_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                logger.info(f"Successfully downloaded FIT file to {fit_file}")
                return fit_file
            else:
                logger.error(f"Failed to download FIT file with status code: {response.status_code}")
                try:
                    logger.error(f"Error response: {response.text}")
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error downloading FIT file: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        return None 