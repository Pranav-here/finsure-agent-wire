"""Data models for news items."""

import re
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
        if not self.domain and self.url:
            from urllib.parse import urlparse
            self.domain = urlparse(self.url).netloc.lower()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "url": self.url,
            "canonical_url": self.canonical_url or self.url,
            "url_hash": self.url_hash or "",
            "title": self.title,
            "description": self.description or "",
            "source": self.source,
            "domain": self.domain or "",
            "published_at": self.published_at.isoformat(),
            "relevance_score": self.relevance_score,
        }
    
    def _truncate_text(self, text: str, max_len: int) -> str:
        """Trim text to a maximum length, adding ellipsis when needed."""
        if len(text) <= max_len:
            return text
        return text[: max_len - 3].rstrip(" ,;:.") + "..."
    
    def _extract_summary(self, max_len: int = 180) -> str:
        """Pull a short summary from description or title."""
        text = (self.description or self.title or "").strip()
        if not text:
            return ""
        
        sentences = re.split(r"(?<=[.!?])\s+", text)
        summary = sentences[0] if sentences else text
        return self._truncate_text(summary, max_len)
    
    def _pick_tone(self) -> str:
        """
        Choose a tone for the tweet based on content keywords.
        
        Returns one of: 'news', 'serious', 'light'
        """
        text = f"{self.title} {self.description or ''}".lower()
        
        serious_keywords = [
            "fraud", "regulation", "regulatory", "breach",
            "lawsuit", "crime", "guilty", "sec ", "fine",
            "compliance", "penalty", "probe",
        ]
        upbeat_keywords = [
            "launch", "introduces", "debuts", "announces",
            "survey", "report", "forecasts", "budget",
            "funding", "round", "earnings", "expands",
            "autonomous", "agents", "ai", "cloud",
        ]
        
        if any(kw in text for kw in serious_keywords):
            return "serious"
        if any(kw in text for kw in upbeat_keywords):
            return "news"
        
        if self.url_hash:
            tones = ["news", "serious", "light"]
            return tones[int(self.url_hash, 16) % len(tones)]
        return "news"
    
    def format_tweet(self, max_length: int = 280) -> str:
        """
        Format item as a tweet with a short summary and tone-aware template.
        
        Tones:
            - news: concise headline-style
            - serious: cautionary or weighty items
            - light: slightly playful TL;DR
        """
        link = self.canonical_url or self.url
        title = (self.title or "").strip()
        summary = self._extract_summary(max_len=140)
        
        if summary.lower() == title.lower():
            summary = ""
        
        tone = self._pick_tone()
        
        templates = {
            "news": "AI+finance brief: {summary} | {title}. {link}",
            "serious": "Heads-up: {summary} | {title}. Read: {link}",
            "light": "Quick take: {summary} ({title}) {link}",
        }
        
        template = templates.get(tone, templates["news"])
        
        def build(summary_text: str) -> str:
            summary_part = summary_text if summary_text else title
            return template.format(summary=summary_part, title=title, link=link).strip()
        
        tweet = build(summary)
        
        if len(tweet) > max_length and summary:
            room = max_length - (len(tweet) - len(summary))
            if room > 20:
                shortened = self._truncate_text(summary, room)
                tweet = build(shortened)
        
        if len(tweet) > max_length:
            compact = f"{title} - {link}"
            if len(compact) > max_length:
                available = max_length - len(link) - 3  # room for separator and ellipsis
                compact = f"{self._truncate_text(title, available)} - {link}"
            tweet = compact[:max_length]
        
        return tweet
