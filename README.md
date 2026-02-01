# AI Agents in Finance News Autoposter

An automated news aggregator that discovers and shares recent developments in AI agents applied to finance and insurance. The system collects content from multiple sources, filters for relevance, and posts curated items to X (Twitter).

## Overview

This project continuously monitors news about AI agents in the finance and insurance sectors from several legitimate sources:

- **arXiv Research Papers** - Academic publications from Cornell University's repository
- **Premium Financial News** - WSJ, Financial Times, Reuters, American Banker, Insurance Journal
- **Tech Publications** - MIT Technology Review, Wired AI, TechCrunch, VentureBeat
- **GDELT API** - Global news aggregator covering the last 24 hours
- **YouTube Data API** - Long-form videos only (4+ minutes, Shorts filtered out)

The system uses dual-keyword relevance scoring to ensure items match both AI agent technology and finance/insurance topics. Content is deduplicated using URL canonicalization and SQLite tracking to prevent reposting.

For details on how the system works and what data it reads, see [HOW_IT_WORKS.md](./HOW_IT_WORKS.md).

## Features

- Collects recent news from the last 24 hours (configurable)
- Dual-keyword matching: items must be relevant to both AI agents AND finance/insurance
- URL canonicalization plus in-run deduplication that collapses repeated links and keeps the highest-quality version
- Domain rate limiting to ensure diversity (max 1 post per domain per run)
- Source credibility scoring with boosts for academic papers and premium news
- Tone-aware tweet generator (news/serious/light) that summarizes the article so posts are less bland
- DRY_RUN and REVIEW_MODE for safe testing
- Scheduled execution via GitHub Actions or manual runs
- Detailed logging with metrics on collection, filtering, and posting

## Quick Start

### Prerequisites

- Python 3.11 or higher
- X (Twitter) Developer Account with API credentials
- YouTube Data API v3 key (optional but recommended)
- Git and GitHub account (for scheduled deployment)

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/pranav-here/finsure-agent-wire.git
   cd finsure-agent-wire
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

4. Test in DRY RUN mode (safe, no actual posting):
   ```bash
   python scripts/run_once.py
   ```

5. Review the output and adjust configuration as needed

6. Enable live posting after testing:
   ```bash
   # Set DRY_RUN=false in .env
   python scripts/run_once.py
   ```

## Configuration

### Required Environment Variables

Copy `.env.example` to `.env` and configure the following:

**X (Twitter) API Credentials** (OAuth 1.0a):
```bash
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_SECRET=your_access_token_secret
```

See [API_CREDENTIALS.md](./API_CREDENTIALS.md) for detailed setup instructions.

**YouTube API** (optional):
```bash
YOUTUBE_API_KEY=your_youtube_api_v3_key
```

The free tier provides 10,000 units per day. Each search uses 100 units. Running every 6 hours uses approximately 400 units per day.

**RSS Feeds** (optional):
```bash
RSS_FEEDS=https://medium.com/feed/tag/fintech,https://techcrunch.com/feed/
```

### Operational Settings

```bash
DRY_RUN=true                    # Set to false for live posting
REVIEW_MODE=false               # Set to true to print drafts without posting
LOOKBACK_HOURS=24               # Only fetch items from last N hours
MAX_POSTS_PER_RUN=5            # Maximum tweets per execution
MAX_POSTS_PER_DOMAIN=1         # Prevent domain monopolization
MIN_SCORE_THRESHOLD=5.0        # Minimum relevance score to post
```

### Optional Configuration

```bash
# Database
DB_PATH=./data/autoposter.db

# Logging
LOG_LEVEL=INFO

# YouTube search queries (comma-separated)
YOUTUBE_QUERIES=AI agents finance,autonomous agents banking,LLM fintech

# Scoring weights
AGENT_KEYWORD_WEIGHT=1.0
FINANCE_KEYWORD_WEIGHT=1.0
RECENCY_WEIGHT=0.5
```

## GitHub Actions Deployment

### Setup

1. Add repository secrets in GitHub:
   - Go to Settings → Secrets and variables → Actions → New repository secret
   - Add each credential from your `.env` file:
     - `X_API_KEY`
     - `X_API_SECRET`
     - `X_ACCESS_TOKEN`
     - `X_ACCESS_SECRET`
     - `YOUTUBE_API_KEY` (if using YouTube)

2. Push to GitHub:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

3. The workflow will run automatically based on the schedule, or you can trigger it manually from the Actions tab.

### Customize Schedule

Edit `.github/workflows/publish.yml`:
```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours (default)
  # - cron: '0 */3 * * *'   # Every 3 hours
  # - cron: '0 8,16 * * *'  # 8am and 4pm daily
  # - cron: '0 9 * * 1-5'   # 9am weekdays only
```

## Project Structure

```
finsure-agent-wire/
├── src/finsure_agent_wire/
│   ├── __init__.py
│   ├── config.py           # Pydantic settings and environment variables
│   ├── models.py           # NewsItem dataclass
│   ├── db.py               # SQLite schema and deduplication
│   ├── scoring.py          # Dual-keyword relevance scoring
│   ├── pipeline.py         # Main orchestration logic
│   ├── x_client.py         # X API v2 client with OAuth 1.0a
│   └── sources/
│       ├── __init__.py
│       ├── arxiv.py        # arXiv research paper integration
│       ├── gdelt.py        # GDELT DOC API integration
│       ├── youtube.py      # YouTube Data API v3 integration
│       └── rss.py          # RSS/Medium feed parser
├── scripts/
│   ├── run_once.py         # Main entry point
│   └── test_scoring.py     # Scoring validation script
├── .github/workflows/
│   └── publish.yml         # GitHub Actions workflow
├── data/                   # Created at runtime (SQLite DB)
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── HOW_IT_WORKS.md        # Technical deep-dive
├── SETUP.md               # Detailed setup guide
└── API_CREDENTIALS.md     # API key setup instructions
```

## Testing and Validation

### Test Relevance Scoring

```bash
python scripts/test_scoring.py
```

This prints scores for sample titles to validate keyword tuning.

### Dry Run

```bash
# Ensure DRY_RUN=true in .env
python scripts/run_once.py
```

Check logs for:
- Items fetched per source
- Items filtered by age and relevance
- Deduplication statistics
- Tweet drafts (if REVIEW_MODE enabled)

## Observability

Each run logs detailed metrics:
```
[INFO] === Starting News Collection ===
[INFO] GDELT: Fetched 234 articles
[INFO] YouTube: Fetched 12 videos
[INFO] RSS: Fetched 45 articles
[INFO] Total items before filtering: 291
[INFO] Filtered by age (>24h): 87
[INFO] Filtered by relevance (score < 5.0): 154
[INFO] After deduplication: 38 unique items
[INFO] Top 5 items selected for posting
[INFO] Posted 0 tweets (DRY_RUN enabled)
```

Errors are logged with context:
```
[ERROR] X API Error: 429 Rate Limit - Retry in 15 minutes
[WARNING] YouTube API quota exceeded - skipping video search
```

## Safety Features

1. **DRY_RUN mode** (default) - Test without posting
2. **REVIEW_MODE** - Print tweet drafts for manual approval
3. **24-hour filter** - Never post stale news
4. **Domain rate limiting** - Prevent outlet monopolization
5. **URL canonicalization** - Strip tracking parameters before hashing
6. **Deduplication** - SQLite tracks posted URLs to prevent duplicates
7. **Max posts per run** - Configurable ceiling on posting volume

## Tweet Formatting

Tweets follow a clean, professional format:
```
{Title} — {Context Phrase} {URL}
```

Example:
```
Anthropic launches agent-based fraud detection for banks — New autonomous system processes insurance claims in real-time https://example.com/article
```

Constraints:
- Always 280 characters or less
- Context derived only from title and description
- Clean URLs with canonicalization
- Professional tone

## Troubleshooting

### X API Errors

**403 Forbidden**:
- Verify app has "Read and Write" permissions
- Regenerate Access Token after changing permissions

**429 Rate Limited**:
- Free tier allows 50 posts per 24 hours
- Bot includes exponential backoff and retries

**401 Unauthorized**:
- Verify all 4 credentials in `.env`
- Check for extra spaces or quotes

### YouTube API

**Quota Exceeded**:
- Free tier: 10,000 units per day
- Each search uses 100 units
- Running every 6 hours uses approximately 400 units per day

### No Items Found

- Check `LOOKBACK_HOURS` (default 24)
- Lower `MIN_SCORE_THRESHOLD` temporarily
- Run `test_scoring.py` to validate keywords

## Advanced Configuration

### Custom Keywords

Edit `src/finsure_agent_wire/scoring.py`:

```python
AI_KEYWORDS = [
    'agent', 'agents', 'agentic', 'autonomous',
    'multi-agent', 'llm agent', 'ai agent',
    # Add your keywords...
]

FINANCE_KEYWORDS = [
    'fintech', 'insurtech', 'banking', 'trading',
    # Add your keywords...
]
```

### Custom Scoring Weights

In `.env`:
```bash
AGENT_KEYWORD_WEIGHT=1.5       # Boost AI agent matches
FINANCE_KEYWORD_WEIGHT=1.0     # Standard finance weight
RECENCY_WEIGHT=0.3             # Slight recency boost
```

## Contributing

Improvements are welcome:

1. Fork the repository
2. Create a feature branch
3. Add tests if applicable
4. Submit a pull request with clear description

## License

MIT License - free to use for personal or commercial projects.

## Documentation

- [HOW_IT_WORKS.md](./HOW_IT_WORKS.md) - Technical deep-dive into system architecture
- [SETUP.md](./SETUP.md) - Complete setup guide
- [API_CREDENTIALS.md](./API_CREDENTIALS.md) - API key setup instructions
- [DATA_QUALITY.md](./DATA_QUALITY.md) - Source legitimacy and quality details
