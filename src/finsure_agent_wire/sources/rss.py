"""RSS feed parser for Medium and generic RSS sources."""

import logging
from datetime import datetime, timezone, timedelta
from typing import List
from email.utils import parsedate_to_datetime

import feedparser

from ..models import NewsItem

logger = logging.getLogger(__name__)


def parse_rss_date(date_str: str) -> datetime:
    """
    Parse RSS date string to datetime.
    
    Handles multiple formats: RFC 2822, ISO 8601, etc.
    
    Args:
        date_str: Date string from RSS feed
        
    Returns:
        Parsed datetime with UTC timezone
    """
    try:
        # Try RFC 2822 format (most common in RSS)
        dt = parsedate_to_datetime(date_str)
        # Ensure UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        pass
    
    # Try ISO 8601
    for fmt in ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d']:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            continue
    
    # Fallback to now
    logger.warning(f"Could not parse date: {date_str}, using current time")
    return datetime.now(timezone.utc)


def fetch_rss_feed(url: str, lookback_hours: int = 24) -> List[NewsItem]:
    """
    Fetch and parse a single RSS feed.
    
    Args:
        url: RSS feed URL
        lookback_hours: Only include items from last N hours
        
    Returns:
        List of NewsItems from this feed
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    
    try:
        logger.info(f"Fetching RSS feed: {url}")
        
        feed = feedparser.parse(url)
        
        if feed.bozo:
            # Feed has errors but may still be parseable
            logger.warning(f"RSS feed has errors: {url} - {feed.bozo_exception}")
        
        entries = feed.get('entries', [])
        logger.info(f"RSS feed returned {len(entries)} entries: {url}")
        
        items = []
        for entry in entries:
            try:
                # Get publication date (try multiple fields)
                date_str = entry.get('published') or entry.get('updated') or entry.get('created')
                if date_str:
                    pub_date = parse_rss_date(date_str)
                else:
                    # No date, use now
                    pub_date = datetime.now(timezone.utc)
                
                # Filter by cutoff
                if pub_date < cutoff:
                    continue
                
                # Get URL
                link = entry.get('link', '')
                if not link:
                    continue
                
                # Get title
                title = entry.get('title', 'Untitled')
                
                # Get description (try multiple fields)
                description = (
                    entry.get('summary') or 
                    entry.get('description') or 
                    entry.get('content', [{}])[0].get('value', '') if entry.get('content') else ''
                )
                
                item = NewsItem(
                    url=link,
                    title=title,
                    description=description,
                    source='rss',
                    published_at=pub_date,
                )
                
                items.append(item)
            
            except Exception as e:
                logger.warning(f"Error parsing RSS entry: {e}")
                continue
        
        logger.info(f"RSS: {len(items)} items from {url} after date filtering")
        return items
    
    except Exception as e:
        logger.error(f"Error fetching RSS feed {url}: {e}")
        return []


def fetch_rss_feeds(feed_urls: List[str], lookback_hours: int = 24) -> List[NewsItem]:
    """
    Fetch and parse multiple RSS feeds.
    
    Args:
        feed_urls: List of RSS feed URLs
        lookback_hours: Only include items from last N hours
        
    Returns:
        Combined list of NewsItems from all feeds
    """
    if not feed_urls:
        logger.info("No RSS feeds configured, skipping RSS fetch")
        return []
    
    all_items = []
    
    for url in feed_urls:
        items = fetch_rss_feed(url, lookback_hours=lookback_hours)
        all_items.extend(items)
    
    logger.info(f"RSS: Total {len(all_items)} items from {len(feed_urls)} feeds")
    return all_items
