import logging
import time
from datetime import datetime, timezone
from typing import List, Optional

import feedparser

from ..config import Settings
from ..models import Item

logger = logging.getLogger(__name__)


def _parse_time_struct(ts) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(time.mktime(ts), tz=timezone.utc)
    except Exception:
        return None


def _collect_feeds(settings: Settings) -> List[str]:
    feeds = list(settings.rss_feeds)
    for tag in settings.medium_tags:
        feeds.append(f"https://medium.com/feed/tag/{tag}")
    for pub in settings.medium_publications:
        feeds.append(f"https://medium.com/feed/{pub}")
    return [f for f in feeds if f]


def fetch_rss(settings: Settings, cutoff: datetime) -> List[Item]:
    feeds = _collect_feeds(settings)
    if not feeds:
        logger.info("No RSS feeds configured; skipping")
        return []

    items: List[Item] = []
    for feed_url in feeds:
        try:
            parsed = feedparser.parse(feed_url)
        except Exception as exc:
            logger.error("RSS fetch failed for %s: %s", feed_url, exc)
            continue

        for entry in parsed.entries:
            title = (entry.get("title") or "").strip()
            link = entry.get("link")
            summary = (entry.get("summary") or entry.get("description") or "").strip()
            published_at = (
                _parse_time_struct(entry.get("published_parsed"))
                or _parse_time_struct(entry.get("updated_parsed"))
            )
            if not title or not link or not published_at:
                continue
            if published_at < cutoff:
                continue
            items.append(
                Item(
                    source="rss",
                    title=title,
                    description=summary,
                    url=link,
                    published_at=published_at,
                )
            )
    logger.info("RSS returned %d items across %d feeds", len(items), len(feeds))
    return items


__all__ = ["fetch_rss"]
