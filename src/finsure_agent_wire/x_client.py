"""X (Twitter) API v2 client with OAuth 1.0a authentication."""

import logging
import time
from typing import Optional

import requests
from requests_oauthlib import OAuth1

logger = logging.getLogger(__name__)


class XAPIError(Exception):
    """Custom exception for X API errors."""
    pass


class XClient:
    """Client for X API v2 with OAuth 1.0a user context."""
    
    BASE_URL = "https://api.twitter.com/2"
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_secret: str,
    ):
        """
        Initialize X API client.
        
        Args:
            api_key: X API Key (Consumer Key)
            api_secret: X API Secret (Consumer Secret)
            access_token: X Access Token
            access_secret: X Access Token Secret
        """
        self.auth = OAuth1(
            api_key,
            api_secret,
            access_token,
            access_secret,
        )
        self.session = requests.Session()
        self.session.auth = self.auth
    
    def create_tweet(
        self,
        text: str,
        max_retries: int = 3,
        retry_delay: int = 5,
    ) -> dict:
        """
        Create a tweet using X API v2.
        
        Args:
            text: Tweet text (max 280 characters)
            max_retries: Number of retry attempts on failure
            retry_delay: Initial delay between retries (seconds)
            
        Returns:
            API response dictionary with tweet data
            
        Raises:
            XAPIError: If tweet creation fails after retries
        """
        if len(text) > 280:
            raise ValueError(f"Tweet text exceeds 280 characters: {len(text)}")
        
        url = f"{self.BASE_URL}/tweets"
        payload = {"text": text}
        
        for attempt in range(max_retries):
            try:
                response = self.session.post(url, json=payload)
                
                # Success
                if response.status_code == 201:
                    data = response.json()
                    tweet_id = data.get('data', {}).get('id')
                    logger.info(f"Tweet posted successfully: {tweet_id}")
                    return data
                
                # Rate limit - wait and retry
                elif response.status_code == 429:
                    reset_time = response.headers.get('x-rate-limit-reset')
                    if reset_time:
                        wait_seconds = int(reset_time) - int(time.time())
                        wait_seconds = max(wait_seconds, retry_delay)
                    else:
                        wait_seconds = retry_delay * (2 ** attempt)
                    
                    logger.warning(
                        f"Rate limited (429). Waiting {wait_seconds}s before retry {attempt + 1}/{max_retries}"
                    )
                    time.sleep(wait_seconds)
                    continue
                
                # Other errors
                else:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get('detail') or error_data.get('title') or response.text
                    
                    logger.error(
                        f"X API Error ({response.status_code}): {error_msg}"
                    )
                    
                    # Don't retry client errors (except 429)
                    if 400 <= response.status_code < 500:
                        raise XAPIError(f"Client error {response.status_code}: {error_msg}")
                    
                    # Retry server errors
                    if attempt < max_retries - 1:
                        wait_seconds = retry_delay * (2 ** attempt)
                        logger.info(f"Retrying in {wait_seconds}s... ({attempt + 1}/{max_retries})")
                        time.sleep(wait_seconds)
                        continue
                    
                    raise XAPIError(f"Server error {response.status_code}: {error_msg}")
            
            except requests.RequestException as e:
                logger.error(f"Network error: {e}")
                
                if attempt < max_retries - 1:
                    wait_seconds = retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {wait_seconds}s... ({attempt + 1}/{max_retries})")
                    time.sleep(wait_seconds)
                    continue
                
                raise XAPIError(f"Network error after {max_retries} attempts: {e}")
        
        raise XAPIError(f"Failed to post tweet after {max_retries} attempts")
    
    def verify_credentials(self) -> bool:
        """
        Verify API credentials by fetching authenticated user info.
        
        Returns:
            True if credentials are valid
            
        Raises:
            XAPIError: If credentials are invalid
        """
        url = f"{self.BASE_URL}/users/me"
        
        try:
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                username = data.get('data', {}).get('username')
                logger.info(f"Credentials verified for user: @{username}")
                return True
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('detail') or error_data.get('title') or response.text
                raise XAPIError(f"Credential verification failed ({response.status_code}): {error_msg}")
        
        except requests.RequestException as e:
            raise XAPIError(f"Network error during verification: {e}")
