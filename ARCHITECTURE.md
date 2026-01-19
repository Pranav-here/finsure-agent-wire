# System Architecture

## Overview

The finsure-agent-wire system is a Python-based news aggregation pipeline that collects, filters, and posts content about AI agents in finance and insurance. The architecture follows a modular design with clear separation of concerns.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FINSURE AGENT WIRE                          │
│              AI Agents in Finance News Autoposter                │
└─────────────────────────────────────────────────────────────────┘

                              ┌──────────┐
                              │ TRIGGER  │
                              │(Schedule/│
                              │ Manual)  │
                              └────┬─────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │   run_once.py (Entry Point) │
                    │  - Load Config from .env    │
                    │  - Setup Logging            │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  pipeline.py (Orchestrator) │
                    └──────────────┬──────────────┘
                                   │
        ┌──────────────────────────┴──────────────────────────┐
        │                                                      │
        ▼                                                      ▼
┌───────────────┐                                    ┌─────────────────┐
│ 1. COLLECT    │                                    │ 5. DEDUPLICATE  │
│               │                                    │                 │
│ ┌───────────┐ │                                    │ ┌─────────────┐ │
│ │  GDELT    │ │────┐                          ┌────│ │ SQLite DB   │ │
│ │  DOC API  │ │    │                          │    │ │ url_hash    │ │
│ └───────────┘ │    │                          │    │ │ index       │ │
│               │    │                          │    │ └─────────────┘ │
│ ┌───────────┐ │    │       ┌───────────┐     │    │                 │
│ │  YouTube  │ │────┼──────▶│ NewsItem  │─────┤    │ • Canonical URL │
│ │ Data API  │ │    │       │  Objects  │     │    │ • Hash tracking │
│ └───────────┘ │    │       └───────────┘     │    │ • Remove dupes  │
│               │    │                          │    └─────────────────┘
│ ┌───────────┐ │    │                          │
│ │   arXiv   │ │────┤                          │            │
│ │    API    │ │    │                          │            │
│ └───────────┘ │    │                          │            │
│               │    │                          │            │
│ ┌───────────┐ │    │                          │            │
│ │    RSS    │ │────┘                          │            │
│ │  Feeds    │ │                               │            │
│ └───────────┘ │              │                │            │
└───────────────┘              │                │            │
                               ▼                │            ▼
                    ┌──────────────────┐        │    ┌──────────────┐
                    │ 2. SCORE         │        │    │ 6. RANK      │
                    │                  │        │    │              │
                    │ scoring.py       │        │    │ • By score   │
                    │                  │        │    │   (DESC)     │
                    │ • AI keywords    │        │    │ • By recency │
                    │ • Finance        │        │    │   (DESC)     │
                    │   keywords       │        │    └──────┬───────┘
                    │ • Both required  │        │           │
                    │ • Exclusion list │        │           │
                    └────────┬─────────┘        │           ▼
                             │                  │  ┌──────────────────┐
                             ▼                  │  │ 7. SELECT        │
                    ┌──────────────────┐        │  │                  │
                    │ 3. FILTER        │        │  │ Rate Limits:     │
                    │                  │        │  │ • Max N/run      │
                    │ • Min score      │        │  │ • Max 1/domain   │
                    │   threshold      │        │  └────────┬─────────┘
                    │ • Remove low     │        │           │
                    │   relevance      │        │           │
                    └────────┬─────────┘        │           ▼
                             │                  │  ┌──────────────────┐
                             ▼                  │  │ 8. POST          │
                    ┌──────────────────┐        │  │                  │
                    │ 4. CANONICALIZE  │        │  │ • Format tweet   │
                    │                  │        │  │ • X API v2       │
                    │ • Strip UTM      │        │  │ • OAuth 1.0a     │
                    │ • Normalize URL  │────────┘  │ • Retry logic    │
                    │ • Generate hash  │           │ • Mark as posted │
                    └──────────────────┘           └──────────────────┘
```

## Data Model

### NewsItem Object

The core data structure used throughout the pipeline:

```python
NewsItem
├── url: str              # Original URL
├── canonical_url: str    # Cleaned URL (no tracking params)
├── url_hash: str         # SHA-256 hash for deduplication
├── title: str            # Article/video title
├── description: str      # Summary or description
├── source: str           # Source type: 'gdelt', 'youtube', 'rss', 'arxiv'
├── domain: str           # Extracted from URL
├── published_at: datetime # Publication timestamp
└── relevance_score: float # Calculated relevance (0.0+)
```

## Components

### 1. Data Sources

Located in `src/finsure_agent_wire/sources/`

#### GDELT (`gdelt.py`)

Fetches news articles from the GDELT project's DOC API.

- **Endpoint**: `https://api.gdeltproject.org/api/v2/doc/doc`
- **Query**: Broad search combining AI agent and finance keywords
- **Time Filter**: `timespan` parameter (e.g., "24h")
- **Returns**: Articles with URL, title, and seen date
- **Rate Limits**: No strict limits, but reasonable use expected

####YouTube (`youtube.py`)

Searches for videos using YouTube Data API v3.

- **API**: YouTube Data API v3
- **Method**: `search.list`
- **Filters**:
  - `type=video`
  - `order=date` (most recent first)
  - `videoDuration=medium` (excludes videos under 4 minutes)
  - `publishedAfter` (ISO 8601 timestamp)
- **Quota**: 100 units per search request
- **Additional Filtering**: Checks for "shorts" in title/description

#### arXiv (`arxiv.py`)

Fetches research papers from Cornell's arXiv repository.

- **Endpoint**: `http://export.arxiv.org/api/query`
- **Query**: Searches across all fields for AI + finance topics
- **Format**: Atom XML feed
- **Returns**: Papers with title, abstract, authors, publication date
- **Rate Limits**: No official limit, but 1-2 requests per run typical

#### RSS (`rss.py`)

Parses RSS/Atom feeds from various news sources.

- **Library**: feedparser
- **Format Support**: RSS 2.0, Atom, RSS 1.0
- **Date Parsing**: RFC 2822, ISO 8601, and other formats
- **Sources**: Medium, TechCrunch, financial news outlets, and custom feeds

### 2. Relevance Scoring

Located in `src/finsure_agent_wire/scoring.py`

#### Scoring Algorithm

The system uses multiplicative dual-keyword matching:

```python
# Keyword matching
ai_matches = count_keyword_matches(text, AI_KEYWORDS)
finance_matches = count_keyword_matches(text, FINANCE_KEYWORDS)

# Base score (multiplicative to enforce both requirements)
base_score = (ai_matches * agent_weight) * (finance_matches * finance_weight)

# Source credibility boost
source_boost = {
    'arxiv': 10.0,      # Academic papers
    'premium_rss': 5.0,  # WSJ, Reuters, etc.
    'default': 0.0       # GDELT, YouTube
}

# Recency boost (slight preference for newer content)
recency_boost = calculate_recency_boost(published_at)

# Final score
total_score = base_score + source_boost + recency_boost
```

#### Keyword Sets

**AI Keywords** (38 total):
- General AI: ai, artificial intelligence, machine learning, deep learning
- LLMs: llm, large language model, gpt, generative ai
- Agents: agent, agents, agentic, autonomous, multi-agent
- Frameworks: langchain, langgraph, autogen, crewai
- Capabilities: tool use, orchestration, planning, reasoning

**Finance Keywords** (39 total):
- Industry: fintech, insurtech, banking, finance, insurance
- Processes: underwriting, claims, fraud detection, trading
- Compliance: kyc, aml, regulatory, compliance
- Products: lending, credit, mortgage, payment, policy

**Exclusion Keywords**:
- Off-topic: sports, celebrity, gossip, entertainment
- Non-AI: travel agent
- Clickbait: passive income, get rich, easy money

#### Requirements

- Must match at least 1 AI keyword
- Must match at least 1 finance keyword
- If either count is 0, score is 0 (filtered out)
- Must not match any exclusion keyword

### 3. Database

Located in `src/finsure_agent_wire/db.py`

#### Schema

```sql
CREATE TABLE posted_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_hash TEXT UNIQUE NOT NULL,
    canonical_url TEXT NOT NULL,
    original_url TEXT,
    title TEXT,
    source TEXT,
    domain TEXT,
    published_at TEXT,
    posted_at TEXT,
    relevance_score REAL
);

CREATE INDEX idx_url_hash ON posted_items(url_hash);
```

#### URL Canonicalization

Normalizes URLs to detect duplicates:

1. Parse URL into components
2. Remove tracking parameters:
   - UTM parameters (utm_source, utm_medium, etc.)
   - Social media trackers (fbclid, gclid, etc.)
   - Analytics parameters (ref, source, campaign, etc.)
3. Lowercase the domain
4. Remove trailing slashes
5. Remove URL fragments (#section)
6. Normalize http to https for known domains

#### Deduplication Process

1. Canonicalize the URL
2. Generate SHA-256 hash of canonical URL
3. Query database for existing hash
4. If found, skip item
5. If not found, add to posted items after successful posting

### 4. X (Twitter) Client

Located in `src/finsure_agent_wire/x_client.py`

#### Authentication

Uses OAuth 1.0a with four credentials:
- API Key (Consumer Key)
- API Secret (Consumer Secret)
- Access Token
- Access Token Secret

#### API Interaction

- **Endpoint**: `POST https://api.twitter.com/2/tweets`
- **Library**: requests with requests-oauthlib
- **Content Type**: application/json

#### Features

- Exponential backoff retry (3 attempts)
- Rate limit handling (429 response → wait and retry)
- Credential verification before posting
- Clean error messages with context
- DRY_RUN mode support (doesn't actually post)

### 5. Pipeline Orchestration

Located in `src/finsure_agent_wire/pipeline.py`

#### Execution Flow

1. **Collection Phase**
   - Fetch from all enabled sources in parallel
   - Combine into single list of NewsItems
   - Log counts per source

2. **Filtering Phase**
   - Remove items outside time window (LOOKBACK_HOURS)
   - Calculate relevance scores for all items
   - Filter items below MIN_SCORE_THRESHOLD
   - Log filtering statistics

3. **Deduplication Phase**
   - Canonicalize all URLs
   - Generate hashes
   - Query database for existing hashes
   - Remove duplicates
   - Log deduplication statistics

4. **Ranking Phase**
   - Sort by relevance score (descending)
   - Sort by recency for ties
   - Prepare ordered list for selection

5. **Selection Phase**
   - Take top N items (MAX_POSTS_PER_RUN)
   - Apply domain rate limiting (MAX_POSTS_PER_DOMAIN)
   - Ensure diversity across sources

6. **Posting Phase**
   - Format each item as a tweet
   - Post via X API
   - Record in database
   - Handle errors gracefully

#### Safety Modes

**DRY_RUN Mode** (DRY_RUN=true):
- Executes entire pipeline
- Logs what would be posted
- Does not call X API
- Does not mark items as posted in database

**REVIEW_MODE** (REVIEW_MODE=true):
- Prints formatted tweet drafts
- Pauses for manual review
- Requires user confirmation before posting

### 6. Configuration

Located in `src/finsure_agent_wire/config.py`

Uses Pydantic Settings for:
- Environment variable loading from `.env`
- Type validation
- Default values
- Helper methods (parsing comma-separated lists)

Key configuration parameters:
- `lookback_hours`: Time window for collection (default: 24)
- `max_posts_per_run`: Global posting limit (default: 5)
- `max_posts_per_domain`: Per-domain limit (default: 1)
- `min_score_threshold`: Minimum relevance score (default: 5.0)
- Scoring weights for fine-tuning

## Deployment Architecture

### Local Execution

```
User Machine
├── Python 3.11+
├── .env file (credentials)
├── SQLite database (data/autoposter.db)
└── Manual execution: python scripts/run_once.py
```

### GitHub Actions

```
GitHub Runner (ubuntu-latest)
├── Python 3.11
├── Environment secrets (credentials)
├── Scheduled trigger: cron '0 */6 * * *'
├── Manual trigger: workflow_dispatch
└── Ephemeral SQLite database (rebuilt each run)
```

Note: In GitHub Actions, the SQLite database doesn't persist between runs, creating a fresh instance each time. For persistence, consider using a cloud database.

## Error Handling

### Graceful Degradation

- If one source fails, others continue
- If YouTube quota exceeded, skip YouTube
- If RSS feed broken, skip that feed
- Database errors logged but don't stop pipeline

### Retry Logic

- X API: 3 attempts with exponential backoff (1s, 2s, 4s)
- Network errors: Automatic retry via requests library
- Rate limits: Calculate wait time from headers and retry

### Logging

Log levels:
- **INFO**: High-level progress and metrics
- **DEBUG**: Detailed item-level decisions
- **WARNING**: Recoverable errors
- **ERROR**: Critical failures

All errors include context (source, item title, error message).

## Security Considerations

### Credentials

- Never commit `.env` to version control
- Use GitHub Secrets for Actions deployment
- API keys not logged or exposed
- OAuth tokens stored securely

### Data Privacy

- Only public news content processed
- No personal data collected
- SQLite database contains only URLs and metadata
- No tracking of users

## Performance Characteristics

### Typical Execution

- **Total runtime**: 10-30 seconds
- **Collection**: 5-15 seconds (parallel API calls)
- **Scoring**: <1 second
- **Database operations**: <1 second
- **Posting**: 2-5 seconds (sequential, with retries)

### Resource Usage

- **Memory**: <50 MB typical
- **Disk**: SQLite database grows ~1 KB per posted item
- **Network**: ~5-10 API requests per run
- **API Quotas**: Well within free tiers

## Scalability Considerations

Current design is optimized for:
- Posting 3-10 items every 6 hours
- Handling 200-500 collected items per run
- Running on free-tier services

For higher volume:
- Consider cloud database for persistence
- Implement distributed collection
- Add caching layer for repeated queries
- Use async/await for parallel API calls

## Extensibility

The modular design allows easy extension:

### Adding New Sources

1. Create new file in `src/finsure_agent_wire/sources/`
2. Implement function returning `List[NewsItem]`
3. Add to pipeline collection phase
4. Update configuration if needed

### Custom Scoring

1. Modify keywords in `scoring.py`
2. Adjust weights in `.env`
3. Implement custom scoring functions as needed

### Different Posting Platforms

1. Create new client module (similar to `x_client.py`)
2. Implement posting interface
3. Update pipeline to use new client

This architecture provides a solid foundation for automated news curation while remaining flexible for future enhancements.
