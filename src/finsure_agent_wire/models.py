"""Data models for news items."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class NewsItem:
    """Represents a news article, video, or RSS item."""
    
    # Required fields
    url: str
    title: str
    source: str  # 'gdelt', 'youtube', 'rss'
    published_at: datetime
    
    # Optional fields
    description: Optional[str] = None
    domain: Optional[str] = None
    canonical_url: Optional[str] = None
    url_hash: Optional[str] = None
    
    # Scoring
    relevance_score: float = 0.0
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Extract domain from URL if not provided
        if not self.domain and self.url:
            from urllib.parse import urlparse
            self.domain = urlparse(self.url).netloc.lower()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            'url': self.url,
            'canonical_url': self.canonical_url or self.url,
            'url_hash': self.url_hash or '',
            'title': self.title,
            'description': self.description or '',
            'source': self.source,
            'domain': self.domain or '',
            'published_at': self.published_at.isoformat(),
            'relevance_score': self.relevance_score,
        }
    
    def format_tweet(self, max_length: int = 280) -> str:
        """
        Format item as a tweet.
        
        Format: {Title} — {Context} {URL}
        
        Context is derived from description if available, otherwise empty.
        Total length must be <= max_length.
        """
        # Use canonical URL if available
        link = self.canonical_url or self.url
        
        # Start with title
        tweet = self.title.strip()
        
        # Try to add context from description
        context = ""
        if self.description:
            desc = self.description.strip()
            # Take first sentence or first 100 chars
            if '.' in desc:
                context = desc.split('.')[0].strip()
            else:
                context = desc[:100].strip()
            
            # Clean up context
            if context and context != tweet:
                context = f" — {context}"
        
        # Assemble tweet
        tweet_with_context = f"{tweet}{context} {link}"
        
        # Truncate if needed
        if len(tweet_with_context) > max_length:
            # Remove context and try again
            tweet_without_context = f"{tweet} {link}"
            if len(tweet_without_context) > max_length:
                # Truncate title
                available = max_length - len(link) - 4  # " ..." + space
                tweet = f"{tweet[:available]}... {link}"
            else:
                tweet = tweet_without_context
        else:
            tweet = tweet_with_context
        
        return tweet[:max_length]
