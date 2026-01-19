# Setup Guide

This guide walks through setting up the AI finance news autoposter from scratch.

## Step 1: Get X (Twitter) API Credentials

The bot requires X API credentials to post tweets. You'll need four values.

### Create a Developer Account

1. Visit https://developer.twitter.com/en/portal/dashboard
2. Sign in with your Twitter account
3. If prompted, apply for a developer account (usually approved immediately)

### Create a Project and App

1. Click "Create Project"
2. Fill in project details:
   - Name: "AI Finance News Bot" (or your choice)
   - Use case: "Making a bot"
   - Description: "Automated news aggregator"
3. Create an app within the project:
   - App name: Must be unique (e.g., "finsure-agent-wire-yourname")
   - Click "Complete"

### Get API Keys

After creating the app, you'll see your **API Key** and **API Key Secret**. Save these immediately - you won't see them again.

### Set Permissions

This step is critical:

1. Go to your app settings
2. Find "User authentication settings" and click "Set up"
3. Configure:
   - **App permissions**: Select "Read and Write" (required for posting)
   - **Type of App**: "Web App, Automated App or Bot"
   - **Callback URI**: `http://localhost` (not used but required)
   - **Website URL**: Your GitHub repo URL
4. Save changes

### Generate Access Tokens

1. Go to the "Keys and tokens" tab
2. Under "Access Token and Secret", click "Generate"
3. Save both the **Access Token** and **Access Token Secret**

Important: If you change app permissions after generating tokens, you must regenerate the access tokens.

You should now have:
- API Key
- API Key Secret
- Access Token
- Access Token Secret

## Step 2: Get YouTube API Key (Optional)

The YouTube Data API v3 key is optional but recommended for including videos in your feed.

### Create a Google Cloud Project

1. Visit https://console.cloud.google.com
2. Click the project dropdown (top left)
3. Click "New Project"
4. Enter project name: "finsure-agent-wire"
5. Click "Create" and wait for project creation

### Enable YouTube Data API

1. Search for "YouTube Data API v3" in the search bar
2. Click on the API
3. Click "Enable"
4. Wait for activation

### Create API Key

1. Navigate to "Credentials" from the left sidebar
2. Click "Create Credentials" and select "API Key"
3. Copy the generated API key

### Restrict Key (Recommended)

1. Click on your API key name
2. Under "API restrictions", select "Restrict key"
3. Check only "YouTube Data API v3"
4. Click "Save"

The free tier provides 10,000 quota units per day. Each search costs 100 units, so running every 6 hours uses about 400 units daily.

## Step 3: Configure Environment

1. Copy the example configuration:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your credentials:
   ```bash
   # X API credentials (required)
   X_API_KEY=your_api_key_here
   X_API_SECRET=your_api_secret_here
   X_ACCESS_TOKEN=your_access_token_here
   X_ACCESS_SECRET=your_access_token_secret_here

   # YouTube API (optional)
   YOUTUBE_API_KEY=your_youtube_key_here

   # Keep DRY_RUN enabled for initial testing
   DRY_RUN=true
   ```

3. Save the file

Note: Never commit `.env` to version control. It's already in `.gitignore`.

## Step 4: Install Dependencies

Install required Python packages:

```bash
pip install -r requirements.txt
```

Requirements include:
- `requests` - HTTP client
- `feedparser` - RSS feed parsing
- `google-api-python-client` - YouTube API
- `pydantic` - Configuration validation
- `pydantic-settings` - Environment variable management

## Step 5: Test the Setup

### Test Scoring System

Validate that the relevance scoring works as expected:

```bash
python scripts/test_scoring.py
```

You should see scored examples showing how different titles are evaluated for relevance.

### Run in Dry Mode

Execute a test run without actually posting:

```bash
python scripts/run_once.py
```

Expected output:
```
[INFO] === Starting News Collection ===
[INFO] GDELT: Fetched 234 articles
[INFO] YouTube: Fetched 12 videos
[INFO] RSS: Fetched 45 articles
[INFO] Total items collected: 291
[INFO] Filtered by relevance: 38 items passed
[INFO] After deduplication: 35 unique items
[INFO] DRY_RUN mode: Would post 5 tweets (not actually posting)
```

Review the logs to ensure:
- Items are being collected from sources
- Relevance filtering is working
- Tweet drafts look reasonable

## Step 6: Enable Live Posting

Once you're satisfied with the test results:

1. Edit `.env`:
   ```bash
   DRY_RUN=false
   ```

2. Run again:
   ```bash
   python scripts/run_once.py
   ```

3. Check your X profile to verify the tweets were posted

## Step 7: Deploy to GitHub Actions

To run the bot automatically on a schedule:

### Push to GitHub

```bash
git add .
git commit -m "Initial setup"
git push origin main
```

### Add Repository Secrets

1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add each secret:
   - `X_API_KEY`
   - `X_API_SECRET`
   - `X_ACCESS_TOKEN`
   - `X_ACCESS_SECRET`
   - `YOUTUBE_API_KEY` (if using YouTube)

### Verify Workflow

The workflow file `.github/workflows/publish.yml` is already configured to:
- Run every 6 hours
- Use secrets from GitHub
- Execute with DRY_RUN disabled

You can:
- Monitor runs in the Actions tab
- Trigger manual runs if needed
- View logs for each execution

## Troubleshooting

### X API Returns 401 Unauthorized

Cause: Incorrect credentials

Fix:
- Double-check all four credentials in `.env`
- Ensure no extra spaces or quotes
- Verify you copied the complete token strings

### X API Returns 403 Forbidden

Cause: App lacks write permissions

Fix:
1. Go to app settings on Twitter Developer Portal
2. Edit "User authentication settings"
3. Change to "Read and Write" permissions
4. Save changes
5. Regenerate access token and secret (critical step)
6. Update `.env` with new tokens

### YouTube API Returns 403

Cause: API not enabled or quota exceeded

Fix:
- Verify "YouTube Data API v3" is enabled in Google Cloud Console
- Check quota at https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas
- If over quota, wait 24 hours or temporarily remove the YouTube API key

### No Items Collected

Possible causes:
- Network connectivity issues
- GDELT API temporarily unavailable (rare)
- Lookback window too short

Solutions:
- Check internet connection
- Increase `LOOKBACK_HOURS` to 48 for testing
- Try running again after a few minutes

### All Items Filtered

Cause: Relevance threshold too high or keyword mismatch

Fix:
- Lower `MIN_SCORE_THRESHOLD` in `.env` (try 3.0)
- Run `python scripts/test_scoring.py` to understand scoring
- Review and adjust keywords in `src/finsure_agent_wire/scoring.py`

## Configuration Options

### Change Posting Frequency

Edit `.github/workflows/publish.yml`:
```yaml
schedule:
  - cron: '0 */3 * * *'  # Every 3 hours
  # - cron: '0 8,16 * * *'  # 8am and 4pm daily
  # - cron: '0 9 * * 1-5'  # 9am weekdays only
```

### Add RSS Feeds

Edit `.env`:
```bash
RSS_FEEDS=https://medium.com/feed/tag/fintech,https://techcrunch.com/feed/,https://example.com/feed.xml
```

### Adjust Scoring

Edit `.env`:
```bash
AGENT_KEYWORD_WEIGHT=1.5
FINANCE_KEYWORD_WEIGHT=1.0
MIN_SCORE_THRESHOLD=6.0
```

### Customize Keywords

Edit `src/finsure_agent_wire/scoring.py` to add domain-specific keywords relevant to your focus area.

## Next Steps

1. Monitor the bot for the first few days
2. Adjust `MIN_SCORE_THRESHOLD` based on content quality
3. Add or remove RSS feeds as you discover sources
4. Tune keywords to match your interests
5. Consider adding custom exclude keywords if you notice unwanted content

For more details, see:
- [README.md](./README.md) - Project overview
- [HOW_IT_WORKS.md](./HOW_IT_WORKS.md) - Technical architecture
- [API_CREDENTIALS.md](./API_CREDENTIALS.md) - Detailed API setup
- [DATA_QUALITY.md](./DATA_QUALITY.md) - Source quality information
