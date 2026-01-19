# 🏗️ System Architecture

## High-Level Overview

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
                    │ • Agent keywords │        │    │ • By recency │
                    │ • Finance        │        │    │   (DESC)     │
                    │   keywords       │        │    └──────┬───────┘
                    │ • BOTH required  │        │           │
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

## Data Flow

### NewsItem Object
```python
NewsItem
├── url: str              # Original URL
├── canonical_url: str    # Cleaned URL (no tracking params)
├── url_hash: str         # SHA-256 hash for dedup
├── title: str
├── description: str
├── source: str           # 'gdelt', 'youtube', 'rss'
├── domain: str           # Extracted from URL
├── published_at: datetime
└── relevance_score: float
```

## Component Details

### 1. Sources (`src/finsure_agent_wire/sources/`)

#### GDELT (`gdelt.py`)
- **Endpoint**: `https://api.gdeltproject.org/api/v2/doc/doc`
- **Query**: Broad search for AI agents + finance keywords
- **Time Filter**: `timespan` parameter (e.g., "24h")
- **Output**: Article list with URL, title, seendate

#### YouTube (`youtube.py`)
- **API**: YouTube Data API v3
- **Method**: `search.list`
- **Filters**: 
  - `type=video`
  - `order=date`
  - `publishedAfter` (ISO 8601)
  - Custom queries from config
- **Quota**: 100 units per search

#### RSS (`rss.py`)
- **Library**: feedparser
- **Supports**: Medium, TechCrunch, custom feeds
- **Date Parsing**: RFC 2822, ISO 8601
- **Filter**: Published/updated in last 24h

### 2. Scoring (`scoring.py`)

**Dual-Keyword Matching (Multiplicative)**:
```
base_score = (agent_matches × agent_weight) × (finance_matches × finance_weight)
total_score = base_score + recency_boost
```

**Requirements**:
- Must have ≥1 agent keyword
- Must have ≥1 finance keyword
- If either = 0, score = 0 (filtered out)

**Keywords**:
- **Agent**: agent, agents, agentic, autonomous, multi-agent, LangChain, tool-use, etc.
- **Finance**: fintech, insurtech, banking, fraud, KYC, underwriting, claims, etc.
- **Exclusions**: sports, celebrity, gossip, travel agent, etc.

### 3. Database (`db.py`)

**Schema**:
```sql
CREATE TABLE posted_items (
    id INTEGER PRIMARY KEY,
    url_hash TEXT UNIQUE,      -- SHA-256 of canonical URL
    canonical_url TEXT,         -- Cleaned URL
    original_url TEXT,          -- Raw URL
    title TEXT,
    source TEXT,
    domain TEXT,
    published_at TEXT,
    posted_at TEXT,
    relevance_score REAL
)

CREATE INDEX idx_url_hash ON posted_items(url_hash);
```

**URL Canonicalization**:
- Remove UTM params (`utm_source`, `utm_medium`, etc.)
- Remove tracking params (`fbclid`, `gclid`, etc.)
- Lowercase domain
- Strip trailing slashes
- Remove URL fragments
- Normalize http → https for known domains

### 4. X Client (`x_client.py`)

**Authentication**: OAuth 1.0a
- API Key + API Secret
- Access Token + Access Secret

**Endpoint**: `POST https://api.twitter.com/2/tweets`

**Features**:
- Exponential backoff retry
- Rate limit handling (429 → wait)
- Credential verification
- Clean error messages

### 5. Pipeline (`pipeline.py`)

**Orchestration Steps**:
1. **Collect** → Fetch from all sources
2. **Score** → Calculate relevance
3. **Filter** → Remove low-scoring items
4. **Canonicalize** → Clean URLs and hash
5. **Deduplicate** → Check against database
6. **Rank** → Sort by score + recency
7. **Select** → Apply rate limits
8. **Post** → Tweet + mark as posted

**Safety Modes**:
- `DRY_RUN=true` → Log what would be posted
- `REVIEW_MODE=true` → Print drafts for manual approval

## Configuration (`config.py`)

**Pydantic Settings** with:
- Environment variable loading (`.env`)
- Type validation
- Default values
- Helper methods (parse comma-separated lists)

**Key Settings**:
- `lookback_hours`: Time window for news
- `max_posts_per_run`: Global rate limit
- `max_posts_per_domain`: Per-domain rate limit
- `min_score_threshold`: Minimum relevance score
- Scoring weights for tuning

## Deployment

### Local
```bash
python scripts/run_once.py
```

### GitHub Actions
```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours

env:
  X_API_KEY: ${{ secrets.X_API_KEY }}
  # ... other secrets
```

**Runs on**: `ubuntu-latest`
**Python**: 3.11
**Triggers**: Schedule + Manual

## Observability

**Logging Levels**:
- `INFO`: High-level progress (counts, summaries)
- `DEBUG`: Detailed item-level decisions
- `WARNING`: Recoverable errors (API quota, parsing failures)
- `ERROR`: Critical failures

**Logged Metrics**:
- Items fetched per source
- Items filtered by age/relevance/duplicates
- Items selected for posting
- Items successfully posted
- Database statistics
- API errors with context

## Error Handling

**Graceful Degradation**:
- If one source fails, others continue
- If YouTube quota exceeded, skip videos
- If RSS feed broken, skip that feed
- Database errors → logged but pipeline continues

**Retries**:
- X API: 3 attempts with exponential backoff
- Network errors: Automatic retry
- Rate limits: Wait and retry (calculated from headers)

## Security

**Secrets Management**:
- Never commit `.env` (in `.gitignore`)
- Use GitHub Secrets for Actions
- OAuth tokens stored securely
- No API keys in logs

**Data Privacy**:
- Only public news content
- No personal data collected
- SQLite DB tracks URLs only (no user data)

---

This architecture ensures:
✅ **Reliability**: Graceful error handling  
✅ **Quality**: Dual-keyword filtering + deduplication  
✅ **Safety**: DRY_RUN and REVIEW modes  
✅ **Maintainability**: Modular design, clean logging  
✅ **Scalability**: Rate limits, efficient database  
