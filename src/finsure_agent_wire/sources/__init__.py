"""Sources package for news aggregation."""

from .gdelt import fetch_gdelt_articles
from .youtube import fetch_youtube_videos
from .rss import fetch_rss_feeds

__all__ = [
    'fetch_gdelt_articles',
    'fetch_youtube_videos',
    'fetch_rss_feeds',
]
