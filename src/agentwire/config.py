from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseSettings, Field, validator

# Load environment as early as possible for local runs
load_dotenv()


class Settings(BaseSettings):
    """Runtime configuration pulled from environment variables."""

    lookback_hours: int = Field(default=24, ge=1, description="Hours to look back for fresh content")
    min_score: float = Field(default=2.0, ge=0, description="Minimum relevance score required to post")
    max_posts_per_run: int = Field(default=5, ge=1)
    max_per_domain_per_run: int = Field(default=1, ge=1)

    dry_run: bool = Field(default=True, description="If true, do not post to X")
    review_mode: bool = Field(
        default=True, description="If true, only print drafts even when dry_run is False"
    )
    log_level: str = Field(default="INFO")

    # Sources
    gdelt_query: str = Field(
        default="(ai agent OR agentic OR autonomous agent) AND (finance OR insurance OR fintech OR insurtech)"
    )
    gdelt_max_records: int = Field(default=75, ge=1, le=250)

    youtube_api_key: Optional[str] = None
    youtube_queries: List[str] = Field(
        default_factory=lambda: [
            "ai agents finance",
            "agentic ai trading",
            "ai agents insurance",
        ]
    )

    rss_feeds: List[str] = Field(default_factory=list)
    medium_tags: List[str] = Field(default_factory=lambda: ["ai-agents", "fintech", "insurtech"])
    medium_publications: List[str] = Field(default_factory=list)

    # Scoring
    agent_keywords: List[str] = Field(
        default_factory=lambda: [
            "agent",
            "agents",
            "agentic",
            "multi-agent",
            "autonomous",
            "tool use",
            "planner",
            "orchestration",
            "langgraph",
            "langchain",
            "crew ai",
            "openai o1",
        ]
    )
    finance_keywords: List[str] = Field(
        default_factory=lambda: [
            "finance",
            "fintech",
            "bank",
            "banking",
            "trading",
            "hedge fund",
            "wealth",
            "robo-advisor",
            "payment",
            "credit",
            "loan",
            "mortgage",
            "insurance",
            "insurtech",
            "underwriting",
            "claims",
            "fraud",
            "risk",
            "compliance",
            "kyc",
            "aml",
            "policy",
            "premium",
            "actuary",
        ]
    )
    exclude_keywords: List[str] = Field(
        default_factory=lambda: [
            "sport",
            "celebrity",
            "astrology",
            "horoscope",
            "dating",
            "music video",
            "gaming",
            "movie",
        ]
    )
    weight_agent: float = Field(default=2.0, ge=0)
    weight_finance: float = Field(default=1.5, ge=0)

    # Posting
    x_api_key: Optional[str] = None
    x_api_secret: Optional[str] = None
    x_access_token: Optional[str] = None
    x_access_secret: Optional[str] = None

    database_path: Path = Field(default=Path("data/state.sqlite"))

    @validator(
        "youtube_queries",
        "rss_feeds",
        "medium_tags",
        "medium_publications",
        "agent_keywords",
        "finance_keywords",
        "exclude_keywords",
        pre=True,
        always=True,
    )
    def _split_comma(cls, value):
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value

    @validator("database_path", pre=True)
    def _coerce_path(cls, value):
        return Path(value)

    @property
    def cutoff_iso(self) -> str:
        """ISO timestamp for APIs that require RFC3339."""
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.lookback_hours)
        return cutoff.isoformat()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Treat env vars as plain strings (avoid JSON parsing errors for comma-separated lists)
        @classmethod
        def parse_env_var(cls, field_name, raw_val):
            return raw_val


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    return settings


__all__ = ["Settings", "get_settings"]
