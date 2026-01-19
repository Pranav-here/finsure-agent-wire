# 🤖💰 AI Agents in Finance News Autoposter

**Continuously discover and share the latest AI agent innovations in finance and insurance**

## 🎯 Repository Name Suggestions

1. **finsure-agent-wire** ⭐ (Current - Finance/Insurance Agent Newswire)
2. **agent-finance-radar** (Agent Finance Detection System)
3. **finai-agent-feed** (Financial AI Agent Feed)
4. **insurtech-agent-pulse** (Insurtech Agent News Pulse)
5. **agentic-fin-news** (Agentic Finance News Bot)
6. **finagent-autoposter** (Financial Agent Autoposter)
7. **ai-finance-scout** (AI Finance News Scout)
8. **agents-in-finance** (Agents in Finance News Hub)

---

## 📋 Overview

This bot automatically:
- ✅ **Collects** recent news (last 24 hours) about AI agents in finance/insurance from multiple sources
- ✅ **Filters** using dual-keyword relevance scoring (AI agents + finance/insurance)
- ✅ **Deduplicates** using URL canonicalization and SQLite state tracking
- ✅ **Posts** top items to X (Twitter) with clean, professional formatting
- ✅ **Rate-limits** to maintain quality (max posts per run, max 1 per domain)
- ✅ **Runs** locally or on GitHub Actions schedule

### 🎯 Sources

1. **GDELT DOC API** - Global news aggregator (24h timespan)
2. **YouTube Data API v3** - Video content (publishedAfter filter)
3. **RSS/Medium Feeds** - Direct feeds from finance/insurtech publications

### 🧠 Relevance Scoring

Items must match **BOTH** signal categories:
- **AI Agent Signals**: agent, agents, agentic, autonomous, multi-agent, LLM, LangChain, LangGraph, tool-use, orchestration, planner, etc.
- **Finance/Insurance Signals**: fintech, insurtech, banking, trading, underwriting, claims, fraud, risk, compliance, KYC, AML, policy, premium, etc.

Hard-filtered exclusions: sports, celebrity, gossip, astrology, etc.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- X (Twitter) Developer Account with API credentials
- YouTube Data API v3 key (optional, free tier)
- Git & GitHub account (for Actions deployment)

### Local Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/pranav-here/finsure-agent-wire.git
   cd finsure-agent-wire
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials (see Configuration section below)
   ```

4. **Run in DRY RUN mode** (safe, no actual posting)
   ```bash
   python scripts/run_once.py
   ```

5. **Review mode** (prints tweet drafts for manual review)
   ```bash
   # Set REVIEW_MODE=true in .env
   python scripts/run_once.py
   ```

6. **Live posting** (after testing)
   ```bash
   # Set DRY_RUN=false in .env
   python scripts/run_once.py
   ```

---

## ⚙️ Configuration

### Required Environment Variables

Copy `.env.example` to `.env` and configure:

#### X (Twitter) API Credentials (OAuth 1.0a)
```bash
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_SECRET=your_access_token_secret
```

**How to get X API credentials:**
1. Go to [developer.twitter.com](https://developer.twitter.com)
2. Create a Project and App
3. Enable OAuth 1.0a User Authentication
4. Copy API Key, API Secret, Access Token, Access Token Secret
5. Ensure app has "Read and Write" permissions

#### YouTube API (Optional but Recommended)
```bash
YOUTUBE_API_KEY=your_youtube_api_v3_key
```

**How to get YouTube API key:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project
3. Enable "YouTube Data API v3"
4. Create credentials → API Key
5. Free tier: 10,000 units/day (sufficient for hourly runs)

#### RSS Feeds (Optional)
```bash
RSS_FEEDS=https://medium.com/feed/tag/fintech,https://techcrunch.com/feed/
```

#### Operational Settings
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

---

## 🤖 GitHub Actions Deployment

### Setup

1. **Add Secrets to GitHub**
   - Go to: Settings → Secrets and variables → Actions → New repository secret
   - Add each credential from your `.env` file:
     - `X_API_KEY`
     - `X_API_SECRET`
     - `X_ACCESS_TOKEN`
     - `X_ACCESS_SECRET`
     - `YOUTUBE_API_KEY` (if using YouTube)
     - Any other custom env vars

2. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit: AI finance news autoposter"
   git push origin main
   ```

3. **Workflow will run automatically**
   - Default schedule: Every 6 hours
   - Manually trigger: Actions tab → "Publish AI Finance News" → Run workflow

### Customize Schedule

Edit `.github/workflows/publish.yml`:
```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours
  # Examples:
  # - cron: '0 */3 * * *'   # Every 3 hours
  # - cron: '0 8,16 * * *'  # 8am and 4pm daily
  # - cron: '0 9 * * 1-5'   # 9am weekdays only
```

---

## 📁 Project Structure

```
finsure-agent-wire/
├── src/finsure_agent_wire/
│   ├── __init__.py
│   ├── config.py           # Pydantic settings + environment vars
│   ├── models.py           # NewsItem dataclass
│   ├── db.py               # SQLite schema + deduplication
│   ├── scoring.py          # Dual-keyword relevance scoring
│   ├── pipeline.py         # Main orchestration logic
│   ├── x_client.py         # X API v2 client with OAuth 1.0a
│   └── sources/
│       ├── __init__.py
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
└── README.md
```

---

## 🧪 Testing & Validation

### Test Relevance Scoring

```bash
python scripts/test_scoring.py
```

This prints scores for sample titles to validate your keyword tuning.

### Dry Run

```bash
# In .env, ensure DRY_RUN=true
python scripts/run_once.py
```

Check logs for:
- ✅ Items fetched per source
- ✅ Items filtered by age
- ✅ Items filtered by relevance
- ✅ Deduplication stats
- ✅ Tweet drafts (Review Mode)

---

## 📊 Observability

Every run logs:
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
[INFO] DRY_RUN=true: Would post 5 tweets
[INFO] Posted 0 tweets (DRY_RUN enabled)
```

Errors are logged with clear context:
```
[ERROR] X API Error: 429 Rate Limit - Retry in 15 minutes
[WARNING] YouTube API quota exceeded - skipping video search
```

---

## 🔒 Safety Features

1. **DRY_RUN mode** (default) - Test without posting
2. **REVIEW_MODE** - Print tweet drafts for manual approval
3. **Strict 24h filter** - Never post stale news
4. **Domain rate limiting** - Prevent outlet monopolization
5. **URL canonicalization** - Strip UTM params before hashing
6. **Deduplication** - SQLite tracks posted URLs forever
7. **Max posts per run** - Configurable ceiling

---

## 🎨 Tweet Formatting

Clean, professional, non-cringe format:

```
{Title} — {Context Phrase} {URL}
```

**Example:**
```
Anthropic launches agent-based fraud detection for banks — New autonomous system processes insurance claims in real-time https://example.com/article
```

- ✅ Always <= 280 characters
- ✅ Context derived ONLY from title/description (no hallucinations)
- ✅ Clean URLs (canonicalized, no tracking params)
- ✅ Professional tone

---

## 🛠️ Troubleshooting

### X API Errors

**403 Forbidden**
- Check app has "Read and Write" permissions
- Regenerate Access Token after permission change

**429 Rate Limited**
- Free tier: 50 posts/24h
- Bot includes exponential backoff & retries

**401 Unauthorized**
- Verify all 4 credentials in `.env`
- Check for extra spaces or quotes

### YouTube API Quota

- Free tier: 10,000 units/day
- Each search = 100 units
- Runs every 6h = ~400 units/day (safe)

### No Items Found

- Check `LOOKBACK_HOURS` (default 24)
- Lower `MIN_SCORE_THRESHOLD` temporarily
- Run `test_scoring.py` to validate keywords

---

## 📈 Advanced Configuration

### Custom Keywords

Edit `src/finsure_agent_wire/scoring.py`:

```python
AGENT_KEYWORDS = [
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

---

## 🤝 Contributing

This is a production-ready personal bot, but improvements are welcome:

1. Fork the repo
2. Create a feature branch
3. Add tests if applicable
4. Submit a PR with clear description

---

## 📄 License

MIT License - use freely for personal or commercial projects.

---

## 🎯 Next Steps for YOU

### 1. Get X (Twitter) API Credentials
   - Visit: https://developer.twitter.com
   - Create app, enable OAuth 1.0a
   - Copy 4 credentials to `.env`

### 2. Get YouTube API Key (Recommended)
   - Visit: https://console.cloud.google.com
   - Enable YouTube Data API v3
   - Create API key, add to `.env`

### 3. Configure `.env`
   - Copy `.env.example` → `.env`
   - Add your credentials
   - Adjust `LOOKBACK_HOURS`, `MAX_POSTS_PER_RUN`, etc.

### 4. Test Locally
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Test scoring
   python scripts/test_scoring.py
   
   # Dry run
   python scripts/run_once.py
   ```

### 5. Deploy to GitHub Actions
   - Add secrets to GitHub repo settings
   - Push to main branch
   - Workflow runs automatically every 6h

---

**Built with ❤️ for discovering the cutting edge of AI agents in finance & insurance**
