# Data Quality and Source Legitimacy

## Overview

This document describes the data quality measures implemented to ensure only legitimate, high-quality sources are used for content collection.

## Quality Improvements

### YouTube Content Filtering

**Problem**: YouTube Shorts (videos under 60 seconds) often contain low-quality, meme-like content that lacks substantive information.

**Solution**: Multi-layer filtering approach

1. **API-Level Filtering**
   - Parameter: `videoDuration='medium'`
   - Effect: Excludes all videos under 4 minutes
   - Applied at query time, reducing data transfer

2. **Content-Based Filtering**
   - Checks title and description for "shorts" or "#shorts"
   - Skips matching videos even if they pass duration filter
   - Catches edge cases where shorts are longer than typical

3. **Result**: Effectively 0% YouTube Shorts in final results

**Implementation**: See `src/finsure_agent_wire/sources/youtube.py` lines 62 and 74-77

### Premium News Sources

The system integrates content from established, reputable news organizations:

#### Financial News Sources
- **Wall Street Journal** - Major financial newspaper
- **Financial Times** - Global business publication
- **Reuters** - International news organization
- **American Banker** - Banking industry publication
- **Insurance Journal** - Insurance industry publication

#### Technology Publications
- **MIT Technology Review** - Published by MIT, covers emerging technology
- **Wired** - Technology and culture magazine
- **TechCrunch** - Technology and startup news
- **VentureBeat** - Enterprise technology news
- **CoinDesk** - Cryptocurrency and fintech news

### Academic Research Integration

**Source**: arXiv.org (Cornell University)

**Legitimacy Indicators**:
- Papers hosted by a major research university
- Authors typically affiliated with universities or research labs
- Abstracts and papers are moderated for quality
- Standard repository for AI/ML research preprints
- Often cited in peer-reviewed publications

**Search Queries**:
1. "artificial intelligence finance"
2. "autonomous agents trading"
3. "machine learning insurance"
4. "AI financial services"
5. "agentic systems banking"

**Configuration**: Default maximum of 25 results per run, filtered to last 24 hours

## Source Quality Tiers

### Tier 1: Highest Authority

| Source Type | Examples | Scoring Boost | Typical Volume |
|-------------|----------|---------------|----------------|
| Academic Papers | arXiv | +10.0 | 5-25/day |
| Major Financial News | WSJ, FT, Reuters | +5.0 | 10-30/day |

### Tier 2: High Quality

| Source Type | Examples | Scoring Boost | Typical Volume |
|-------------|----------|---------------|----------------|
| Tech Publications | MIT Tech Review, Wired | +5.0 | 10-20/day |
| Industry Trade | American Banker, Insurance Journal | +5.0 | 5-15/day |

### Tier 3: Curated Secondary

| Source Type | Examples | Scoring Boost | Typical Volume |
|-------------|----------|---------------|----------------|
| Startup News | TechCrunch, VentureBeat | 0.0 | 10-20/day |
| Aggregated News | GDELT | 0.0 | 50-150/day |
| Curated Video | YouTube (filtered) | 0.0 | 5-20/day |

### Excluded Content

The following types of content are actively filtered out:

- YouTube Shorts (videos under 4 minutes)
- Social media posts without verification
- Content farms and blog spam
- Entertainment and meme content
- Off-topic content (sports, celebrity, etc.)

## Quality Assurance Mechanisms

### 1. Dual-Keyword Matching

All items must match keywords from both categories:

**AI/Agent Keywords** (partial list):
- agent, agents, agentic, autonomous
- machine learning, deep learning, neural network
- llm, large language model, gpt
- multi-agent, tool use, orchestration

**Finance/Insurance Keywords** (partial list):
- finance, fintech, banking, insurance, insurtech
- trading, investment, underwriting, claims
- fraud detection, risk management, compliance
- kyc, aml, lending, payment

Items matching only one category are filtered out, regardless of how strong the match is.

### 2. Exclusion List

Hard filtering for off-topic content:

- **Sports**: football, basketball, baseball, etc.
- **Entertainment**: celebrity, movie, gaming
- **Off-topic**: astrology, recipe, travel agent
- **Clickbait**: passive income, get rich, easy money, side hustle

Any item matching exclusion keywords receives a score of 0.0 and is filtered out.

### 3. Source Credibility Scoring

Academic papers and premium news sources receive scoring boosts:

```python
if source == 'arxiv':
    source_boost = 10.0  # Strong preference for research
elif source == 'rss' and domain in premium_domains:
    source_boost = 5.0   # Boost for verified publishers
else:
    source_boost = 0.0   # Baseline for aggregators
```

Premium domains include: ft.com, reuters.com, bloomberg.com, wsj.com, americanbanker.com, insurancejournal.com, technologyreview.com, wired.com, techcrunch.com, venturebeat.com, coindesk.com

### 4. Minimum Score Threshold

Default threshold: 5.0 (configurable via `MIN_SCORE_THRESHOLD`)

**Example Scores**:
- "Autonomous AI Agents Transform Investment Banking" - Score: ~12-15
- "LangChain Adds Multi-Agent Support for Financial Apps" - Score: ~10-13
- "AI Chatbot Helps with Personal Finance" - Score: ~2-4 (filtered)
- "Celebrity Uses AI Filter" - Score: 0.0 (excluded)

## Expected Content Distribution

### Before Quality Improvements
- Total items collected: ~250-350/day
- Relevant items: 30-50/day
- YouTube Shorts: 10-20% of video content
- Limited tech/AI coverage

### After Quality Improvements
- Total items collected: ~350-450/day
- Relevant items: 40-70/day
- YouTube Shorts: <1% (effectively filtered)
- Comprehensive coverage across finance, tech, and academic sources

### Quality Distribution
```
Academic Papers:     15-20% (highest quality)
Financial News:      35-45% (verified sources)
Tech Publications:   25-35% (curated outlets)
Curated Video:       5-10% (long-form only)
```

## Configuration Options

### Disable YouTube Completely

If you prefer to exclude all YouTube content:

```bash
# Option 1: Remove API key
YOUTUBE_API_KEY=

# Option 2: Clear queries
YOUTUBE_QUERIES=
```

The pipeline will automatically skip YouTube if either is empty.

### Prioritize Research Papers

To increase academic content:

```bash
ARXIV_MAX_RESULTS=50  # Default: 25
MIN_SCORE_THRESHOLD=6.0  # Higher selectivity
```

### Add Custom RSS Feeds

Add trusted sources to your `.env` file:

```bash
RSS_FEEDS=https://existing-feeds.com/feed,https://your-trusted-source.com/feed.xml
```

Potential additions:
- Harvard Business Review
- Stanford HAI News
- Financial Stability Board
- Bank for International Settlements

### Adjust Scoring Sensitivity

Modify in `.env`:

```bash
AGENT_KEYWORD_WEIGHT=1.5  # Increase AI agent importance
FINANCE_KEYWORD_WEIGHT=1.0  # Standard finance weight
MIN_SCORE_THRESHOLD=7.0  # Higher bar for posting
```

## Testing Quality

### 1. Test Scoring System

```bash
python scripts/test_scoring.py
```

Shows how different titles are scored, helping validate keyword effectiveness.

### 2. Run in Dry Mode

```bash
# Set in .env: DRY_RUN=true
python scripts/run_once.py
```

Review collected items without posting:
- Check source distribution
- Validate relevance scores
- Identify any low-quality content slipping through

### 3. Review Mode

```bash
# Set in .env: REVIEW_MODE=true
python scripts/run_once.py
```

Prints formatted tweets for manual review before posting.

### 4. Monitor Source Distribution

Check logs for balanced collection:

```
[INFO] arXiv: Fetched 12 papers
[INFO] GDELT: Fetched 85 articles
[INFO] YouTube: Fetched 8 videos  # Should be lower after filtering
[INFO] RSS: Fetched 52 items       # Should be higher with premium feeds
```

## Source Verification Methods

### arXiv Papers
- Check author affiliations (listed in abstract)
- Verify publication date on arXiv.org
- Review abstract quality and citations

### RSS Feeds
- All feeds from verified publishers
- URLs use official domains
- No aggregator sites or content farms

### YouTube Videos
- Minimum 4-minute duration enforced
- No "shorts" in title or description
- Typically: conference talks, tutorials, expert interviews

## Best Practices

### For Maximum Quality
1. Keep `MIN_SCORE_THRESHOLD` at 5.0 or higher
2. Enable all premium RSS feeds
3. Keep YouTube filtering enabled (or disable entirely)
4. Monitor arXiv papers (highest quality signal)
5. Review posted content weekly and adjust as needed

### For Higher Volume
1. Lower `MIN_SCORE_THRESHOLD` to 3.0-4.0
2. Increase `LOOKBACK_HOURS` to 36-48
3. Add more RSS feeds
4. Increase `MAX_POSTS_PER_RUN`

### For Research Focus
1. Increase `ARXIV_MAX_RESULTS` to 50+
2. Add specific arXiv queries for your domain
3. Reduce or disable YouTube
4. Consider higher weight for academic keywords

## Maintenance

### Regular Checks

- Review posted content weekly
- Adjust keywords if off-topic content appears
- Monitor source distribution for balance
- Update RSS feeds as new quality sources emerge

### Updating Keywords

Edit `src/finsure_agent_wire/scoring.py`:

```python
AI_KEYWORDS = [
    # Add emerging AI terminology
    'your-new-keyword',
]

EXCLUDE_KEYWORDS = [
    # Add patterns you've observed in low-quality content
    'unwanted-pattern',
]
```

### Adding Premium Sources

When adding new RSS feeds:
1. Verify the source is reputable
2. Add to `RSS_FEEDS` in `.env`
3. Consider adding domain to premium list in `scoring.py` for boost

## Quality Metrics

Track these metrics to assess quality:

- **Relevance Rate**: (Items posted / Items collected)
- **Source Distribution**: Percentage from each source type
- **Average Score**: Mean relevance score of posted items
- **Duplicate Rate**: (Duplicates found / Unique items)

Healthy ranges:
- Relevance Rate: 5-15%
- Academic Papers: 15-25% of posted items
- Average Score: 10-20
- Duplicate Rate: 10-30%

## Support

For issues with data quality:

1. Run `test_scoring.py` to validate scoring
2. Check logs for filtering statistics
3. Adjust thresholds and keywords as needed
4. Review [HOW_IT_WORKS.md](./HOW_IT_WORKS.md) for technical details

For adding higher-quality sources:
- Custom web scrapers for regulatory sources
- Academic journal APIs (IEEE, ACM, Springer)
- Corporate research portals
- Premium financial data providers

Contact via GitHub issues for assistance.
