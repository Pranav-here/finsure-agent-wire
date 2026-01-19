import logging
import time
from typing import Optional

import requests
from requests_oauthlib import OAuth1

logger = logging.getLogger(__name__)

X_TWEET_URL = "https://api.twitter.com/2/tweets"


class XClient:
    def __init__(
        self,
        api_key: Optional[str],
        api_secret: Optional[str],
        access_token: Optional[str],
        access_secret: Optional[str],
        retries: int = 3,
        timeout: int = 10,
    ) -> None:
        missing = [k for k, v in {
            "X_API_KEY": api_key,
            "X_API_SECRET": api_secret,
            "X_ACCESS_TOKEN": access_token,
            "X_ACCESS_SECRET": access_secret,
        }.items() if not v]
        if missing:
            raise ValueError(f"Missing X credentials: {', '.join(missing)}")
        self.auth = OAuth1(api_key, api_secret, access_token, access_secret)
        self.retries = retries
        self.timeout = timeout

    def create_tweet(self, text: str) -> dict:
        payload = {"text": text}
        last_exc: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                resp = requests.post(X_TWEET_URL, json=payload, auth=self.auth, timeout=self.timeout)
                if resp.status_code == 429:
                    raise RuntimeError("Rate limited by X API")
                if resp.status_code >= 500:
                    raise RuntimeError(f"X API server error {resp.status_code}: {resp.text}")
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                last_exc = exc
                logger.warning("Tweet attempt %d/%d failed: %s", attempt, self.retries, exc)
                if attempt < self.retries:
                    time.sleep(1.5 * attempt)
        raise RuntimeError(f"Failed to post tweet after retries: {last_exc}")


__all__ = ["XClient"]
