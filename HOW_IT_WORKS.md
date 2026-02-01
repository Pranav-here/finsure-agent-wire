# 🔍 How the Finsure Agent Wire System Works

**A Technical Deep-Dive into Data Collection, Processing, and Quality Assurance**

---

## 📖 Quick Summary

This system collects news about AI agents in finance/insurance from multiple sources, scores them for relevance, filters out low-quality content, and posts the best items to X (Twitter). Here's what it actually reads and processes:

### What the System READS:

| Source | What It Reads | What It DOESN'T Read |
|--------|--------------|---------------------|
| **arXiv Papers** | ✅ Title, Abstract, Authors | ❌ Full paper PDF (not needed for discovery) |
| **YouTube Videos** | ✅ Title, Description, Metadata | ❌ Video transcripts (too expensive/slow) |
| **GDELT News** | ✅ Title, Description/Summary | ❌ Full article content |
| **RSS Feeds** | ✅ Title, Summary/Description | ❌ Full article body |

**⚠️ Important**: The system does **NOT** read video transcripts, full article content, or PDF papers. It relies on **titles, descriptions, and metadata** to identify relevant content, which is sufficient for news discovery and sharing.

### What's new (2026-02-01)

- In-run deduplication now collapses repeated links in the same fetch cycle and keeps the highest-scoring/latest version, eliminating timeline doubles.
- Tweet formatter is tone-aware (news / serious / light) and auto-summarizes the item so posts read less robotic while staying under 280 characters.

---

## 🏗️ System Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. DATA COLLECTION (Parallel API Calls)                    │
├─────────────────────────────────────────────────────────────┤
│  • arXiv API      → Academic papers (title + abstract)      │
│  • GDELT API      → Global news (title + description)       │
│  • YouTube API    → Videos (title + description)            │
│  • RSS Feeds      → Premium news (title + summary)          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. TIME FILTERING                                           │
├─────────────────────────────────────────────────────────────┤
│  • Only keep items from last 24 hours (configurable)        │
│  • Ensures freshness and relevance                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. RELEVANCE SCORING                                        │
├─────────────────────────────────────────────────────────────┤
│  • Scan title + description for AI keywords                 │
│  • Scan title + description for finance/insurance keywords  │
│  • Must have BOTH to pass (multiplicative scoring)          │
│  • Apply source credibility boost                           │
│  • Hard-filter excluded topics (sports, celebrity, etc.)    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. DEDUPLICATION                                            │
├─────────────────────────────────────────────────────────────┤
│  • Canonicalize URLs (remove tracking params)               │
│  • Check SQLite database for previously posted URLs         │
│  • Skip duplicates                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  5. RANKING & SELECTION                                      │
├─────────────────────────────────────────────────────────────┤
│  • Sort by relevance score (highest first)                  │
│  • Apply domain rate limiting (max 1 per domain)            │
│  • Select top N items (default: 5)                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  6. POSTING TO X (TWITTER)                                   │
├─────────────────────────────────────────────────────────────┤
│  • Format tweet (title + context + URL ≤ 280 chars)         │
│  • Post via X API v2 (OAuth 1.0a)                           │
│  • Store in database to prevent re-posting                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 Detailed Component Breakdown

### 1. Data Collection Layer

#### 🎓 arXiv Research Papers

**File**: `src/finsure_agent_wire/sources/arxiv.py`

**What It Reads**:
- ✅ Paper title
- ✅ Abstract (summary)
- ✅ Author names (first 3 + "et al.")
- ✅ Publication date
- ✅ arXiv URL

**How It Works**:
```python
# Constructs API query like:
http://export.arxiv.org/api/query?search_query=all:AI+agents+finance&max_results=50
```

**Example Query**: `"artificial intelligence finance"`

**What Gets Stored**:
```python
NewsItem(
    url="http://arxiv.org/abs/2401.12345",
    title="📄 Autonomous AI Agents for Algorithmic Trading",
    description="[arXiv Paper] Smith et al. — This paper presents...",
    source="arxiv",
    published_at=datetime(2026, 1, 18, 10, 30)
)
```

**Does NOT Read**: Full paper PDF content (not needed for discovery)

---

#### 🌐 GDELT Global News

**File**: `src/finsure_agent_wire/sources/gdelt.py`

**What It Reads**:
- ✅ Article title
- ✅ Article description/summary (provided by GDELT)
- ✅ Publish date ("seen date" in GDELT)
- ✅ Article URL

**How It Works**:
```python
# Calls GDELT DOC 2.0 API with dual-keyword query:
query = '(agent OR agents OR agentic) AND (finance OR fintech OR insurance)'
```

**API Endpoint**: `https://api.gdeltproject.org/api/v2/doc/doc`

**Does NOT Read**: Full article content (only metadata provided by GDELT)

---

#### 🎥 YouTube Videos

**File**: `src/finsure_agent_wire/sources/youtube.py`

**What It Reads**:
- ✅ Video title
- ✅ Video description (truncated snippet from YouTube API)
- ✅ Publish date
- ✅ Video duration (for filtering)
- ✅ Video URL

**How It Works**:
```python
# YouTube Data API v3 search with filters:
youtube.search().list(
    q="AI agents finance",
    type='video',
    videoDuration='medium',  # Excludes videos under 4 minutes
    publishedAfter=cutoff_time
)
```

**Quality Filters Applied**:
1. **API-level**: `videoDuration='medium'` excludes videos under 4 minutes (filters out Shorts)
2. **Content-level**: Checks title/description for "shorts" or "#shorts" and skips them

**Does NOT Read**: 
- ❌ Video transcripts (would require YouTube Transcript API, expensive and slow)
- ❌ Actual video content
- ❌ Comments

**Why No Transcripts?**:
- 🚫 **Cost**: YouTube Transcript API costs quota units per request
- 🚫 **Speed**: Fetching 10+ transcripts adds 5-10 seconds per run
- ✅ **Not Needed**: Title + description are sufficient for relevance detection
- ✅ **Better UX**: We're sharing the video link, not summarizing it

---

#### 📰 RSS Feeds (Premium News)

**File**: `src/finsure_agent_wire/sources/rss.py`

**What It Reads**:
- ✅ Article title
- ✅ Article summary/description (from RSS `<summary>` or `<description>` tag)
- ✅ Publish date
- ✅ Article URL

**Premium Sources**:
- Wall Street Journal
- Financial Times
- Reuters Business
- American Banker
- Insurance Journal
- MIT Technology Review
- Wired (AI section)
- TechCrunch (AI + Fintech)
- VentureBeat (AI)
- CoinDesk

**How It Works**:
```python
# Parses RSS XML feed using feedparser
feed = feedparser.parse("https://www.ft.com/rss/companies/financial-services")
# Extracts: entry.title, entry.summary, entry.published, entry.link
```

**Does NOT Read**: 
- ❌ Full article content (behind paywalls often)
- ❌ Article body text
- ❌ Images or embedded content

**Why Not Full Articles?**:
- 🚫 **Paywalls**: Most premium news is paywalled
- 🚫 **Legal**: Scraping full content may violate terms
- ✅ **Not Needed**: RSS summary is sufficient for relevance
- ✅ **Ethical**: We link to original source for readers

---

### 2. Scoring System

**File**: `src/finsure_agent_wire/scoring.py`

#### How Relevance Scoring Works

**Input**: Combined text from `title + description` of each item

**Step 1: Hard Exclusion Filter**

Immediately filters out items containing:
- Sports keywords: `football`, `soccer`, `basketball`
- Entertainment: `celebrity`, `movie`, `gaming`
- Off-topic: `astrology`, `recipe`, `travel agent`
- Clickbait: `passive income`, `get rich`, `no work`

**Step 2: Dual-Keyword Matching**

**AI Keywords** (39 total):
```python
AI_KEYWORDS = [
    'ai', 'artificial intelligence', 'machine learning', 'deep learning',
    'llm', 'large language model', 'gpt', 'generative ai',
    'agent', 'agents', 'agentic', 'autonomous', 'multi-agent',
    'tool use', 'orchestration', 'langchain', 'langgraph',
    # ... and more
]
```

**Finance/Insurance Keywords** (39 total):
```python
FINANCE_KEYWORDS = [
    'fintech', 'insurtech', 'finance', 'financial', 'banking',
    'insurance', 'underwriting', 'claims', 'fraud detection',
    'trading', 'investment', 'credit', 'lending', 'payment',
    'cryptocurrency', 'blockchain', 'robo-advisor',
    # ... and more
]
```

**Scoring Formula**:
```python
# Count keyword matches
ai_matches = count_matches(text, AI_KEYWORDS)          # e.g., 3
finance_matches = count_matches(text, FINANCE_KEYWORDS) # e.g., 2

# Base score (multiplicative - must have BOTH)
base_score = (ai_matches * 1.0) * (finance_matches * 1.0)  # 3 * 2 = 6.0

# Source credibility boost
if source == 'arxiv':
    source_boost = 10.0  # Research papers prioritized
elif source == 'rss' and domain in premium_domains:
    source_boost = 5.0   # Premium news gets boost
else:
    source_boost = 0.0   # GDELT baseline

# Recency boost (slight preference for newer)
recency_boost = calculate_recency(published_at)  # 0-5 range

# Final score
total_score = base_score + source_boost + recency_boost  # e.g., 6.0 + 5.0 + 2.0 = 13.0
```

**Minimum Threshold**: Default `MIN_SCORE_THRESHOLD=5.0`

**Example Scores**:
| Title | AI Matches | Finance Matches | Base | Source | Total | Result |
|-------|-----------|----------------|------|--------|-------|--------|
| "Autonomous AI Agents Transform Investment Banking" | 4 | 3 | 12.0 | +0 | 12.5 | ✅ Posted |
| "arXiv: Multi-Agent System for Fraud Detection" | 3 | 2 | 6.0 | +10 | 16.8 | ✅ Posted |
| "AI Chatbot Helps with Personal Finance" | 1 | 1 | 1.0 | +0 | 1.5 | ❌ Filtered |
| "Celebrity Uses AI Filter on Instagram" | 1 | 0 | 0.0 | - | 0.0 | ❌ Excluded |

---

### 3. Deduplication

**File**: `src/finsure_agent_wire/db.py`

**How It Works**:

1. **URL Canonicalization**:
   ```python
   # Before: https://example.com/article?utm_source=twitter&ref=123
   # After:  https://example.com/article
   ```
   - Removes tracking parameters (`utm_*`, `ref`, `source`, etc.)
   - Converts to lowercase
   - Removes trailing slashes

2. **SQLite Database**:
   ```sql
   CREATE TABLE posted_items (
       id INTEGER PRIMARY KEY,
       url_hash TEXT UNIQUE,  -- SHA256 of canonicalized URL
       url TEXT,
       title TEXT,
       posted_at TIMESTAMP
   );
   ```

3. **Duplicate Check**:
   - Hash the canonicalized URL
   - Query database for existing hash
   - Skip if already posted

**Why This Matters**:
- Same article from different sources (RSS + GDELT) → Only posted once
- Same URL with different tracking params → Detected as duplicate

---

### 4. Rate Limiting & Selection

**Domain Rate Limiting**:
```python
# Ensure diversity - max 1 post per domain per run
MAX_POSTS_PER_DOMAIN = 1

# Example: Can't post 3 articles from techcrunch.com in one run
# Even if all 3 score highly
```

**Selection Process**:
1. Sort all items by relevance score (descending)
2. Take top N items (default `MAX_POSTS_PER_RUN=5`)
3. Apply domain rate limit filter
4. Final list of items to post

---

### 5. Posting to X (Twitter)

**File**: `src/finsure_agent_wire/x_client.py`

**Tweet Format**:
```
{Title} — {Context Phrase} {URL}
```

**Example**:
```
📄 Autonomous Trading Agents Outperform Humans in Simulated Markets — New research from MIT explores multi-agent systems in finance https://arxiv.org/abs/2401.12345
```

**Constraints**:
- ✅ Must be ≤ 280 characters
- ✅ Context derived ONLY from title/description (no hallucinations)
- ✅ Clean URL (canonicalized)

**Safety Modes**:
- **DRY_RUN=true**: Logs what would be posted, doesn't actually post
- **REVIEW_MODE=true**: Prints tweet drafts for manual approval

---

## 🛡️ Data Quality Assurance

### What Ensures Quality?

| Layer | Mechanism | Purpose |
|-------|-----------|---------|
| **Source Selection** | Only premium publishers + arXiv | High-authority content |
| **YouTube Filtering** | `videoDuration='medium'` + keyword filter | No Shorts, only long-form |
| **Dual-Keyword Scoring** | Must match BOTH AI + Finance | Precise topic matching |
| **Exclude List** | Hard filter for off-topic keywords | Remove noise |
| **Source Boost** | arXiv +10, Premium RSS +5 | Prioritize quality |
| **Min Threshold** | Score ≥ 5.0 required | Quality floor |
| **Domain Rate Limit** | Max 1 per domain per run | Diversity |
| **Deduplication** | URL hash tracking | No repeats |

---

## ❓ Frequently Asked Questions

### Does it read full research papers?

**No.** The system only reads:
- ✅ Paper title
- ✅ Abstract (summary)
- ✅ Author names
- ❌ NOT the full PDF content

**Why?**: The abstract contains sufficient information to determine if the paper is about AI agents in finance. Full PDF parsing would add complexity without improving relevance detection.

---

### Does it read YouTube video transcripts?

**No.** The system only reads:
- ✅ Video title
- ✅ Video description (snippet)
- ✅ Metadata (duration, publish date)
- ❌ NOT the transcript or captions

**Why?**:
1. **Cost**: YouTube Transcript API uses quota
2. **Speed**: Fetching transcripts is slow (5-10 seconds per video)
3. **Not Needed**: Title + description are sufficient for discovery
4. **Better UX**: We're sharing the video link, not summarizing content

**Alternative Considered**: Using YouTube Transcript API was evaluated but rejected due to cost/speed tradeoffs for a news discovery bot.

---

### Does it scrape full article content?

**No.** The system only reads:
- ✅ Article title
- ✅ RSS summary/description (provided by publisher)
- ✅ GDELT description (from GDELT API)
- ❌ NOT the full article body

**Why?**:
1. **Paywalls**: Most premium content is paywalled
2. **Legal**: Scraping full content may violate terms of service
3. **Not Needed**: Summaries are sufficient for relevance scoring
4. **Ethical**: We link to the original source for readers

---

### How does it filter out YouTube Shorts?

**Two-Layer Filter**:

1. **API-Level**:
   ```python
   videoDuration='medium'  # Excludes videos under 4 minutes
   ```

2. **Content-Level**:
   ```python
   if 'shorts' in title.lower() or '#shorts' in description.lower():
       skip()
   ```

**Result**: ~0% YouTube Shorts in results

---

### Can I disable YouTube entirely?

**Yes.** Two options:

**Option 1**: Remove API key
```bash
# In .env
YOUTUBE_API_KEY=
```

**Option 2**: Clear queries
```bash
# In .env
YOUTUBE_QUERIES=
```

The pipeline will automatically skip YouTube if either is empty.

---

### What makes arXiv papers legitimate?

**arXiv Quality Signals**:
- ✅ Hosted by Cornell University
- ✅ Papers are submitted by researchers
- ✅ Minimal moderation (checked for non-spam)
- ✅ Standard for AI/ML research dissemination
- ✅ Authors are typically from universities/labs
- ✅ Papers often cited in peer-reviewed publications

**Verification**:
- Author affiliations listed
- Abstract quality indicates research depth
- Citation count over time (not checked by bot, but available on arXiv.org)

---

### How fresh is the data?

**Default**: Last 24 hours only

**Configurable**:
```bash
LOOKBACK_HOURS=24  # Default
# LOOKBACK_HOURS=48  # 2 days
# LOOKBACK_HOURS=168  # 1 week
```

Each source filters by publish date:
- arXiv: `publishedAfter` parameter
- YouTube: `publishedAfter` parameter
- GDELT: `timespan` parameter (e.g., "24h")
- RSS: Date parsing from feed

---

### What if two sources have the same article?

**Handled by Deduplication**:

1. URL canonicalization strips tracking params
2. Both versions hash to same value
3. First one processed gets posted
4. Second one detected as duplicate and skipped

**Example**:
```
Source 1 (RSS):   https://techcrunch.com/2026/01/18/ai-agents?utm_source=rss
Source 2 (GDELT): https://techcrunch.com/2026/01/18/ai-agents?ref=gdelt

→ Both canonicalize to: https://techcrunch.com/2026/01/18/ai-agents
→ Same hash → Only posted once
```

---

## 🚀 Performance Characteristics

### Typical Run Metrics

**Collection Time**: 5-15 seconds
- arXiv: ~2s per query
- GDELT: ~3s per request
- YouTube: ~2s per query
- RSS: ~1s per feed

**Items Collected**: 250-400 total
- arXiv: 5-25 papers
- GDELT: 50-150 articles
- YouTube: 5-20 videos
- RSS: 40-80 articles

**After Filtering**: 30-70 items
- Time filter: Removes ~60-70%
- Relevance filter: Removes ~40-60%
- Deduplication: Removes ~10-20%

**Posted**: 3-5 items (configurable)

---

## 🔧 Configuration Reference

### Key Environment Variables

```bash
# === Data Sources ===
YOUTUBE_API_KEY=your_key          # Enable/disable YouTube
YOUTUBE_QUERIES=AI agents finance,autonomous agents banking
RSS_FEEDS=https://ft.com/rss,...  # Premium news feeds
ARXIV_QUERIES=AI finance,agents trading  # Research topics

# === Quality Controls ===
MIN_SCORE_THRESHOLD=5.0           # Minimum relevance score
LOOKBACK_HOURS=24                 # Freshness window
MAX_POSTS_PER_RUN=5              # Posting limit
MAX_POSTS_PER_DOMAIN=1           # Diversity limit

# === Safety ===
DRY_RUN=true                      # Test mode (no posting)
REVIEW_MODE=false                 # Manual review mode

# === Scoring Weights ===
AGENT_KEYWORD_WEIGHT=1.0          # AI keyword weight
FINANCE_KEYWORD_WEIGHT=1.0        # Finance keyword weight
RECENCY_WEIGHT=0.5                # Recency boost weight
```

---

## 📊 Data Flow Example

### Real Example: arXiv Paper Discovery

**1. API Query**:
```
http://export.arxiv.org/api/query?search_query=all:AI+agents+finance
```

**2. API Response** (XML):
```xml
<entry>
  <id>http://arxiv.org/abs/2401.12345</id>
  <title>Multi-Agent Systems for Automated Trading</title>
  <summary>This paper explores autonomous AI agents...</summary>
  <published>2026-01-18T10:30:00Z</published>
  <author><name>John Smith</name></author>
</entry>
```

**3. Parsed NewsItem**:
```python
NewsItem(
    url="http://arxiv.org/abs/2401.12345",
    title="📄 Multi-Agent Systems for Automated Trading",
    description="[arXiv Paper] John Smith — This paper explores...",
    source="arxiv",
    published_at=datetime(2026, 1, 18, 10, 30, tzinfo=UTC)
)
```

**4. Scoring**:
```python
text = "Multi-Agent Systems for Automated Trading This paper explores..."

AI matches: "agent", "multi-agent", "ai" → 3 matches
Finance matches: "trading", "automated trading" → 2 matches

base_score = 3 * 2 = 6.0
source_boost = 10.0 (arxiv)
recency_boost = 3.2 (very recent)

total_score = 19.2 ✅ (passes threshold of 5.0)
```

**5. Tweet Draft**:
```
📄 Multi-Agent Systems for Automated Trading — New research explores autonomous AI agents in financial markets http://arxiv.org/abs/2401.12345
```

**6. Posted to X** (if not DRY_RUN)

---

## 🎯 Summary

### What the System IS:
✅ **News Discovery Engine**: Finds recent content about AI agents in finance  
✅ **Metadata Analyzer**: Reads titles, descriptions, summaries  
✅ **Quality Filter**: Applies keyword scoring and source credibility checks  
✅ **Automation Bot**: Posts top items to Twitter automatically  

### What the System IS NOT:
❌ **Content Summarizer**: Does not read full articles/papers/transcripts  
❌ **Web Scraper**: Does not extract content behind paywalls  
❌ **Transcript Analyzer**: Does not process video captions/transcripts  
❌ **Full-Text Search**: Relies on metadata, not full content  

---

## 📞 Further Reading

- **Architecture**: See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for code structure
- **Data Quality**: See [`DATA_QUALITY.md`](./DATA_QUALITY.md) for source legitimacy details
- **Setup Guide**: See [`SETUP.md`](./SETUP.md) for deployment instructions
- **API Credentials**: See [`API_CREDENTIALS.md`](./API_CREDENTIALS.md) for API key setup

---

**Last Updated**: 2026-01-19  
**Version**: 1.0  
**Author**: Finsure Agent Wire Team
