import logging
from datetime import datetime, timezone
from typing import List, Optional, Set

import requests
from dateutil import parser

from ..config import Settings
from ..models import Item

logger = logging.getLogger(__name__)
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"


def _parse_date(raw: str) -> Optional[datetime]:
    try:
        dt = parser.isoparse(raw)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def fetch_youtube(settings: Settings, cutoff: datetime) -> List[Item]:
    if not settings.youtube_api_key:
        logger.info("Skipping YouTube (no API key provided)")
        return []

    published_after = cutoff.isoformat()
    seen_ids: Set[str] = set()
    items: List[Item] = []

    for query in settings.youtube_queries:
        params = {
            "part": "snippet",
            "type": "video",
            "order": "date",
            "q": query,
            "maxResults": 20,
            "publishedAfter": published_after,
            "key": settings.youtube_api_key,
        }
        try:
            resp = requests.get(YOUTUBE_API_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("YouTube fetch failed for query '%s': %s", query, exc)
            continue

        for entry in data.get("items", []):
            vid = entry.get("id", {}).get("videoId")
            snippet = entry.get("snippet") or {}
            title = (snippet.get("title") or "").strip()
            description = (snippet.get("description") or "").strip()
            published_raw = snippet.get("publishedAt")
            published_at = _parse_date(published_raw) if published_raw else None
            if not vid or not title or not published_at:
                continue
            if published_at < cutoff:
                continue
            if vid in seen_ids:
                continue
            seen_ids.add(vid)
            items.append(
                Item(
                    source="youtube",
                    title=title,
                    description=description,
                    url=f"https://www.youtube.com/watch?v={vid}",
                    published_at=published_at,
                )
            )
    logger.info("YouTube returned %d items", len(items))
    return items


__all__ = ["fetch_youtube"]
