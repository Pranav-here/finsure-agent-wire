"""GDELT DOC API integration for news aggregation."""

import logging
from datetime import datetime, timezone, timedelta
from typing import List

import requests

from ..models import NewsItem

logger = logging.getLogger(__name__)


def fetch_gdelt_articles(
    lookback_hours: int = 24,
    max_records: int = 250,
) -> List[NewsItem]:
    """
    Fetch recent articles from GDELT DOC API.
    
    Uses the GDELT DOC 2.0 API to search for articles about AI agents in finance/insurance.
    
    API Docs: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
    
    Args:
        lookback_hours: Only fetch articles from last N hours
        max_records: Maximum number of articles to fetch
        
    Returns:
        List of NewsItems from GDELT
    """
    # Calculate cutoff time
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    
    # GDELT uses format like "24h" or "7d"
    if lookback_hours <= 24:
        timespan = f"{lookback_hours}h"
    else:
        days = lookback_hours // 24
        timespan = f"{days}d"
    
    # Build query
    # We use broad search terms here and rely on scoring to filter
    query = '(agent OR agents OR agentic OR autonomous) AND (finance OR fintech OR insurance OR insurtech OR banking)'
    
    params = {
        'query': query,
        'mode': 'ArtList',
        'maxrecords': max_records,
        'timespan': timespan,
        'format': 'json',
    }
    
    url = 'https://api.gdeltproject.org/api/v2/doc/doc'
    
    try:
        logger.info(f"Fetching GDELT articles (timespan={timespan}, max={max_records})")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        articles = data.get('articles', [])
        
        logger.info(f"GDELT returned {len(articles)} articles")
        
        items = []
        for article in articles:
            try:
                # Parse publication date
                # GDELT provides 'seendate' in format like "20240115T123000Z"
                seendate_str = article.get('seendate', '')
                if seendate_str:
                    # Parse: YYYYMMDDTHHMMSSZ
                    pub_date = datetime.strptime(seendate_str, '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
                else:
                    # Fallback to now if no date
                    pub_date = datetime.now(timezone.utc)
                
                # Filter by cutoff
                if pub_date < cutoff:
                    continue
                
                item = NewsItem(
                    url=article.get('url', ''),
                    title=article.get('title', 'Untitled'),
                    description=article.get('seendescription') or article.get('socialimage', ''),
                    source='gdelt',
                    published_at=pub_date,
                )
                
                items.append(item)
            
            except Exception as e:
                logger.warning(f"Error parsing GDELT article: {e}")
                continue
        
        logger.info(f"GDELT: {len(items)} articles after date filtering")
        return items
    
    except requests.RequestException as e:
        logger.error(f"GDELT API request failed: {e}")
        return []
    
    except Exception as e:
        logger.error(f"Unexpected error fetching GDELT: {e}")
        return []
