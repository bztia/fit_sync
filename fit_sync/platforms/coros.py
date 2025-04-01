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
from typing import Dict, List, Optional

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
        self.cache_dir = Path(os.path.expanduser(cache_dir))
        self.session = requests.Session()
        self.token = None
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def authenticate(self) -> bool:
        """
        Authenticate with the Coros platform.
        
        Returns:
            True if authentication was successful, False otherwise
        """
        logger.info(f"Authenticating with Coros as {self.email}")
        # Stub implementation always returns True
        return True
        
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
                "duration": f"{45 + i * 3}:{i*2:02d}",  # Format as MM:SS
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
                            'Authorization': f"Bearer {self.token}"
                        })
                        
                        # Store the user ID for later use
                        self.user_id = response_data.get('data', {}).get('userId')
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