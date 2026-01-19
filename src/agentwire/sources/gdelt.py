import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import requests
from dateutil import parser

from ..config import Settings
from ..models import Item

logger = logging.getLogger(__name__)


def _parse_gdelt_date(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    # GDELT seendate is often YYYYMMDDHHMMSS
    for fmt in ("%Y%m%d%H%M%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        dt = parser.parse(raw)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        logger.debug("Failed to parse date %s", raw)
        return None


def fetch_gdelt(settings: Settings, cutoff: datetime) -> List[Item]:
    params = {
        "query": settings.gdelt_query,
        "maxrecords": settings.gdelt_max_records,
        "format": "json",
        "timespan": f"{settings.lookback_hours}h",
    }
    try:
        resp = requests.get(
            "https://api.gdeltproject.org/api/v2/doc/doc", params=params, timeout=20
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.error("GDELT fetch failed: %s", exc)
        return []

    articles = data.get("articles") or []
    items: List[Item] = []
    for article in articles:
        url = article.get("url")
        title = (article.get("title") or "").strip()
        seen_date = _parse_gdelt_date(article.get("seendate") or article.get("date"))
        if not url or not title or not seen_date:
            continue
        if seen_date < cutoff:
            continue
        description = (article.get("sourceCommonName") or "").strip()
        items.append(
            Item(
                source="gdelt",
                title=title,
                description=description,
                url=url,
                published_at=seen_date,
            )
        )
    logger.info("GDELT returned %d items (fresh %d)", len(articles), len(items))
    return items


__all__ = ["fetch_gdelt"]
