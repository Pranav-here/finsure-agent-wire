"""YouTube Data API v3 integration for video content."""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..models import NewsItem

logger = logging.getLogger(__name__)


def fetch_youtube_videos(
    api_key: str,
    queries: List[str],
    lookback_hours: int = 24,
    max_results_per_query: int = 10,
) -> List[NewsItem]:
    """
    Fetch recent videos from YouTube Data API v3.
    
    Args:
        api_key: YouTube Data API v3 key
        queries: List of search queries
        lookback_hours: Only fetch videos from last N hours
        max_results_per_query: Max results per search query
        
    Returns:
        List of NewsItems from YouTube
    """
    if not api_key:
        logger.warning("YouTube API key not provided, skipping YouTube search")
        return []
    
    if not queries:
        logger.info("No YouTube queries configured, skipping YouTube search")
        return []
    
    # Calculate cutoff time
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    published_after = cutoff.isoformat().replace('+00:00', 'Z')
    
    items = []
    
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        for query in queries:
            try:
                logger.info(f"Searching YouTube for: {query}")
                
                # Search for videos
                search_response = youtube.search().list(
                    q=query,
                    type='video',
                    part='id,snippet',
                    publishedAfter=published_after,
                    order='date',  # Most recent first
                    maxResults=max_results_per_query,
                ).execute()
                
                videos = search_response.get('items', [])
                logger.info(f"YouTube returned {len(videos)} videos for query: {query}")
                
                for video in videos:
                    try:
                        video_id = video['id']['videoId']
                        snippet = video['snippet']
                        
                        # Parse publish date
                        published_str = snippet.get('publishedAt', '')
                        if published_str:
                            # Format: 2024-01-15T12:30:00Z
                            pub_date = datetime.strptime(published_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
                        else:
                            pub_date = datetime.now(timezone.utc)
                        
                        # Double-check cutoff (API should handle this, but be safe)
                        if pub_date < cutoff:
                            continue
                        
                        item = NewsItem(
                            url=f"https://www.youtube.com/watch?v={video_id}",
                            title=snippet.get('title', 'Untitled'),
                            description=snippet.get('description', ''),
                            source='youtube',
                            published_at=pub_date,
                        )
                        
                        items.append(item)
                    
                    except Exception as e:
                        logger.warning(f"Error parsing YouTube video: {e}")
                        continue
            
            except HttpError as e:
                # Handle quota exceeded or other API errors gracefully
                if e.resp.status == 403:
                    logger.error(f"YouTube API quota exceeded or permission denied: {e}")
                    break  # Stop trying other queries if quota exceeded
                else:
                    logger.error(f"YouTube API error for query '{query}': {e}")
                    continue
            
            except Exception as e:
                logger.error(f"Unexpected error searching YouTube for '{query}': {e}")
                continue
        
        logger.info(f"YouTube: {len(items)} videos fetched")
        return items
    
    except Exception as e:
        logger.error(f"YouTube API initialization failed: {e}")
        return []
