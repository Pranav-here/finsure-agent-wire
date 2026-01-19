import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple
from urllib.parse import urlparse

from .config import get_settings
from .db import Database, db_session
from .models import Item
from .scoring import apply_scoring
from .sources.gdelt import fetch_gdelt
from .sources.rss import fetch_rss
from .sources.youtube import fetch_youtube
from .x_client import XClient

logger = logging.getLogger(__name__)


def format_tweet(item: Item) -> str:
    """Generate a concise tweet under 280 characters."""
    base_text = item.title.strip()
    if item.description:
        snippet = item.description.replace("\n", " ").strip()
        if snippet and snippet.lower() not in base_text.lower():
            base_text = f"{base_text} - {snippet}"

    link = item.canonical_url()
    max_text_len = 280 - len(link) - 1
    if len(base_text) > max_text_len:
        base_text = base_text[: max_text_len - 3].rstrip() + "..."
    return f"{base_text} {link}"


def _filter_and_dedupe(
    items: List[Item], cutoff: datetime, db: Database
) -> Tuple[List[Item], int, int]:
    """Return fresh, unique items plus counts of age-filtered and already-seen."""
    seen_count = 0
    age_filtered = 0
    seen_urls = set()
    fresh: List[Item] = []

    for item in items:
        if item.published_at < cutoff:
            age_filtered += 1
            continue
        canon = item.canonical_url()
        if db.has_seen(canon) or canon in seen_urls:
            seen_count += 1
            continue
        item.url = canon
        item.domain = urlparse(item.url).netloc
        db.mark_seen(item)
        seen_urls.add(item.url)
        fresh.append(item)
    return fresh, age_filtered, seen_count


def _enforce_domain_limits(items: List[Item], max_per_domain: int, max_total: int) -> List[Item]:
    domain_counts: Dict[str, int] = defaultdict(int)
    selected: List[Item] = []

    for item in items:
        domain = item.domain or urlparse(item.url).netloc
        if domain_counts[domain] >= max_per_domain:
            continue
        if len(selected) >= max_total:
            break
        domain_counts[domain] += 1
        selected.append(item)
    return selected


def post_items(items: List[Item], settings, db: Database) -> List[Item]:
    posted: List[Item] = []
    can_post = not settings.dry_run and not settings.review_mode
    client = None
    if can_post:
        try:
            client = XClient(
                settings.x_api_key,
                settings.x_api_secret,
                settings.x_access_token,
                settings.x_access_secret,
            )
        except Exception as exc:
            logger.error("Cannot post to X: %s", exc)
            return []

    for item in items:
        tweet = format_tweet(item)
        if settings.review_mode:
            logger.info("Review draft: %s", tweet)
        elif settings.dry_run:
            logger.info("Dry-run draft: %s", tweet)
        if not can_post:
            continue
        try:
            client.create_tweet(tweet)
            db.mark_posted(item.url)
            posted.append(item)
            logger.info("Posted: %s", item.url)
        except Exception as exc:
            logger.error("Failed to post tweet: %s", exc)
    return posted


def run_pipeline() -> None:
    settings = get_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.lookback_hours)
    logger.info(
        "Starting run. cutoff=%s dry_run=%s review_mode=%s",
        cutoff.isoformat(),
        settings.dry_run,
        settings.review_mode,
    )

    fetchers = {
        "gdelt": fetch_gdelt,
        "youtube": fetch_youtube,
        "rss": fetch_rss,
    }

    raw_counts: Dict[str, int] = {}
    collected: List[Item] = []

    for name, fetcher in fetchers.items():
        items = fetcher(settings, cutoff)
        raw_counts[name] = len(items)
        collected.extend(items)

    with db_session(settings.database_path) as db:
        fresh, age_filtered, already_seen = _filter_and_dedupe(collected, cutoff, db)
        scored = apply_scoring(fresh, settings)
        relevance_filtered = len(fresh) - len(scored)
        limited = _enforce_domain_limits(
            scored, settings.max_per_domain_per_run, settings.max_posts_per_run
        )
        posted = post_items(limited, settings, db)

    logger.info(
        "Fetch counts: %s | age_filtered=%d already_seen=%d relevance_filtered=%d selected=%d posted=%d",
        raw_counts,
        age_filtered,
        already_seen,
        relevance_filtered,
        len(limited),
        len(posted),
    )
    logger.info("Run complete")


__all__ = ["run_pipeline", "format_tweet"]
