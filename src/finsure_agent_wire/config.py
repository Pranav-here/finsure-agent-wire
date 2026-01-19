"""Configuration management using Pydantic Settings and python-dotenv."""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""
    
    # ===========================
    # X (Twitter) API Credentials
    # ===========================
    x_api_key: str = Field(..., description="X API Key")
    x_api_secret: str = Field(..., description="X API Secret")
    x_access_token: str = Field(..., description="X Access Token")
    x_access_secret: str = Field(..., description="X Access Token Secret")
    
    # ===========================
    # YouTube API
    # ===========================
    youtube_api_key: Optional[str] = Field(None, description="YouTube Data API v3 Key")
    youtube_queries: str = Field(
        "AI agents finance,autonomous agents banking,LLM agents fintech,agentic AI insurance",
        description="Comma-separated YouTube search queries"
    )
    
    # ===========================
    # RSS Feeds
    # ===========================
    rss_feeds: str = Field(
        "",
        description="Comma-separated RSS feed URLs"
    )
    
    # ===========================
    # arXiv Research Papers
    # ===========================
    arxiv_queries: str = Field(
        "artificial intelligence finance,autonomous agents trading",
        description="Comma-separated arXiv search queries"
    )
    arxiv_max_results: int = Field(25, description="Max papers per arXiv query", ge=1, le=100)
    
    # ===========================
    # Operational Settings
    # ===========================
    dry_run: bool = Field(True, description="If true, don't actually post tweets")
    review_mode: bool = Field(False, description="If true, print drafts for review")
    lookback_hours: int = Field(24, description="Only fetch items from last N hours", ge=1, le=168)
    max_posts_per_run: int = Field(5, description="Maximum tweets per run", ge=1, le=20)
    max_posts_per_domain: int = Field(1, description="Max posts from single domain per run", ge=1, le=10)
    min_score_threshold: float = Field(5.0, description="Minimum relevance score to post", ge=0.0)
    
    # ===========================
    # Database
    # ===========================
    db_path: Path = Field(Path("./data/autoposter.db"), description="SQLite database path")
    
    # ===========================
    # Logging
    # ===========================
    log_level: str = Field("INFO", description="Logging level")
    
    # ===========================
    # Scoring Weights
    # ===========================
    agent_keyword_weight: float = Field(1.0, description="Weight for AI agent keywords", ge=0.0)
    finance_keyword_weight: float = Field(1.0, description="Weight for finance keywords", ge=0.0)
    recency_weight: float = Field(0.5, description="Weight for recency boost", ge=0.0)
    
    # ===========================
    # GDELT Configuration
    # ===========================
    gdelt_mode: str = Field("ArtList", description="GDELT search mode")
    gdelt_max_records: int = Field(250, description="Max GDELT articles to fetch", ge=1, le=500)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def get_youtube_query_list(self) -> List[str]:
        """Parse comma-separated YouTube queries."""
        if not self.youtube_queries:
            return []
        return [q.strip() for q in self.youtube_queries.split(",") if q.strip()]
    
    def get_rss_feed_list(self) -> List[str]:
        """Parse comma-separated RSS feed URLs."""
        if not self.rss_feeds:
            return []
        return [url.strip() for url in self.rss_feeds.split(",") if url.strip()]
    
    def get_arxiv_query_list(self) -> List[str]:
        """Parse comma-separated arXiv queries."""
        if not self.arxiv_queries:
            return []
        return [q.strip() for q in self.arxiv_queries.split(",") if q.strip()]
    
    def ensure_db_directory(self) -> None:
        """Ensure database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)


# Singleton config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create the global config instance."""
    global _config
    if _config is None:
        _config = Config()
        _config.ensure_db_directory()
    return _config
