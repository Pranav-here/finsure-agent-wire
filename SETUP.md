# 🚀 Quick Setup Guide

This guide will get you from zero to posting AI finance news in under 15 minutes.

## Step 1: Get X (Twitter) API Credentials ⚡

**This is REQUIRED**. The bot needs these 4 credentials to post tweets.

1. **Visit**: https://developer.twitter.com/en/portal/dashboard
2. **Sign in** with your Twitter account
3. **Create a Project**:
   - Click "Create Project"
   - Name: "AI Finance News Bot" (or anything)
   - Use case: Select "Making a bot"
   - Project description: "Automated news aggregator"
4. **Create an App**:
   - App name: "finsure-agent-wire" (or unique name)
   - Click "Complete"
5. **Get API Keys**:
   - Save your **API Key** and **API Key Secret** (you'll only see these once!)
6. **Set Permissions**:
   - Go to your app settings
   - User authentication settings → "Set up"
   - App permissions: **Read and Write** (REQUIRED)
   - Type of App: "Web App, Automated App or Bot"
   - Callback URI: http://localhost (doesn't matter for this bot)
   - Website URL: https://github.com/YOUR_USERNAME/finsure-agent-wire
   - Save
7. **Generate Access Tokens**:
   - Go to "Keys and tokens" tab
   - Under "Access Token and Secret" → Click "Generate"
   - Save your **Access Token** and **Access Token Secret**

You now have all 4 credentials:
- ✅ API Key
- ✅ API Key Secret  
- ✅ Access Token
- ✅ Access Token Secret

---

## Step 2: Get YouTube API Key (Optional but Recommended) 🎥

**This is FREE** and adds YouTube videos to your news feed.

1. **Visit**: https://console.cloud.google.com
2. **Create a project**:
   - Click project dropdown → "New Project"
   - Name: "finsure-agent-wire"
   - Click "Create"
3. **Enable YouTube API**:
   - Search for "YouTube Data API v3" in the search bar
   - Click on it → Click "Enable"
4. **Create API Key**:
   - Go to "Credentials" (left sidebar)
   - Click "Create Credentials" → "API Key"
   - Copy your API key
5. **Optional - Restrict Key**:
   - Click on your API key
   - Under "API restrictions" → Select "Restrict key"
   - Choose "YouTube Data API v3"
   - Save

**Quota**: Free tier gives 10,000 units/day. Each search = 100 units. Running every 6 hours = ~400 units/day. **You're well within limits.**

---

## Step 3: Configure Environment Variables 🔧

1. **Copy the template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env`** with your credentials:
   ```bash
   # Required: X API credentials from Step 1
   X_API_KEY=your_api_key_here
   X_API_SECRET=your_api_secret_here
   X_ACCESS_TOKEN=your_access_token_here
   X_ACCESS_SECRET=your_access_token_secret_here

   # Optional: YouTube API key from Step 2
   YOUTUBE_API_KEY=your_youtube_key_here

   # Keep DRY_RUN=true for testing first!
   DRY_RUN=true
   ```

3. **Save the file**

---

## Step 4: Install and Test 🧪

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Test scoring system**:
   ```bash
   python scripts/test_scoring.py
   ```
   This shows how different article titles are scored. You should see HIGH scores for AI agent + finance articles.

3. **Run in DRY RUN mode** (safe, doesn't post):
   ```bash
   python scripts/run_once.py
   ```
   
   You should see output like:
   ```
   [INFO] === Starting News Collection ===
   [INFO] GDELT: Fetched 234 articles
   [INFO] YouTube: Fetched 12 videos
   [INFO] Total items collected: 246
   [INFO] Filtered by relevance: 38 items passed
   [INFO] After deduplication: 38 unique items
   [INFO] DRY_RUN mode: Would post 5 tweets (not actually posting)
   ```

4. **Review the output**:
   - Check if items are being collected ✅
   - Check if relevance filtering makes sense ✅
   - Check the tweet drafts in logs ✅

---

## Step 5: Go Live 🎉

When you're happy with the test results:

1. **Edit `.env`**:
   ```bash
   DRY_RUN=false
   ```

2. **Run for real**:
   ```bash
   python scripts/run_once.py
   ```

3. **Check your X profile** - you should see new tweets! 🚀

---

## Step 6: Deploy to GitHub Actions ⚙️

Automate the bot to run every 6 hours without you.

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Initial commit: AI finance news autoposter"
   git push origin main
   ```

2. **Add secrets to GitHub**:
   - Go to your repo on GitHub
   - Settings → Secrets and variables → Actions
   - Click "New repository secret" for each:
     - `X_API_KEY` = your X API key
     - `X_API_SECRET` = your X API secret
     - `X_ACCESS_TOKEN` = your X access token
     - `X_ACCESS_SECRET` = your X access token secret
     - `YOUTUBE_API_KEY` = your YouTube key (if using)

3. **Workflow will run automatically**:
   - Every 6 hours (00:00, 06:00, 12:00, 18:00 UTC)
   - Or manually: Actions tab → "Publish AI Finance News" → "Run workflow"

4. **Monitor in Actions tab**:
   - You can see logs of each run
   - Check for errors or rate limits

---

## Troubleshooting 🔧

### "403 Forbidden" from X API
- ✅ Check your app has "Read and Write" permissions
- ✅ Regenerate Access Token after changing permissions
- ✅ Verify all 4 credentials are correct in `.env`

### "429 Rate Limited" from X API
- Free tier: 50 tweets per 24 hours
- Bot includes automatic retry logic
- Consider reducing `MAX_POSTS_PER_RUN` in `.env`

### "No items collected"
- ✅ Check internet connection
- ✅ GDELT API might be temporarily down (rare)
- ✅ Try increasing `LOOKBACK_HOURS` to 48 for testing

### "All items filtered by relevance"
- ✅ Lower `MIN_SCORE_THRESHOLD` in `.env` (try 3.0)
- ✅ Run `python scripts/test_scoring.py` to see scoring examples
- ✅ Adjust keywords in `src/finsure_agent_wire/scoring.py`

### YouTube Quota Exceeded
- Free tier: 10,000 units/day
- Reduce `YOUTUBE_QUERIES` or remove YouTube API key temporarily

---

## Customization Tips 🎨

### Change posting frequency
Edit `.github/workflows/publish.yml`:
```yaml
schedule:
  - cron: '0 */3 * * *'  # Every 3 hours
```

### Add more RSS feeds
Edit `.env`:
```bash
RSS_FEEDS=https://medium.com/feed/tag/fintech,https://techcrunch.com/category/fintech/feed/,https://www.pymnts.com/feed/
```

### Adjust scoring
Edit `.env`:
```bash
AGENT_KEYWORD_WEIGHT=1.5  # Boost AI agent matches
FINANCE_KEYWORD_WEIGHT=1.0
MIN_SCORE_THRESHOLD=6.0  # Higher = more selective
```

### Add more keywords
Edit `src/finsure_agent_wire/scoring.py`:
```python
AGENT_KEYWORDS = [
    'agent', 'agents', 'agentic',
    'your-custom-keyword',
    # ...
]
```

---

## What's Next? 🚀

1. ✅ Monitor your bot for the first few days
2. ✅ Adjust `MIN_SCORE_THRESHOLD` based on quality
3. ✅ Add/remove RSS feeds as you discover sources
4. ✅ Tune keywords to match your specific interests
5. ✅ Share your setup with the community!

---

**Need help?** Check the main README.md for detailed documentation.

**Found a bug?** Open an issue on GitHub.

**Happy with the results?** Star the repo! ⭐
