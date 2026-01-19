# API Credentials Guide

This document provides detailed information on obtaining and configuring the API credentials needed for this project.

## Required APIs

This bot requires credentials from two services:

1. **X (Twitter) API** - Required for posting tweets
2. **YouTube Data API v3** - Optional for including YouTube videos

## X (Twitter) API Setup

You need four credentials to authenticate with the X API:

- `X_API_KEY` (also called "Consumer Key" or "API Key")
- `X_API_SECRET` (also called "Consumer Secret" or "API Key Secret")
- `X_ACCESS_TOKEN` (User access token)
- `X_ACCESS_SECRET` (User access token secret)

### Getting X API Credentials

**URL**: https://developer.twitter.com/en/portal/dashboard

### Step-by-Step Process

**1. Create a Developer Account**
- Sign in with your Twitter account
- Apply for developer access if you haven't already
- Most applications are approved instantly

**2. Create a Project**
- Click "Create Project"
- Project name: Choose any descriptive name (e.g., "AI Finance News Bot")
- Use case: Select "Making a bot"
- Project description: Brief explanation of your bot's purpose

**3. Create an App**
- App name must be globally unique (e.g., "finsure-agent-wire-yourname")
- Complete the app creation process

**4. Save API Keys**
- After creating the app, you'll immediately see your API Key and API Key Secret
- **Copy both now** - they won't be shown again
- Store them securely

**5. Configure Permissions** (Critical)
- Navigate to app Settings
- Find "User authentication settings" and click "Set up"
- App permissions: **Select "Read and Write"**
- Type of App: "Web App, Automated App or Bot"
- Callback URI: `http://localhost` (required field but not used)
- Website URL: Your GitHub repository or project website
- Save changes

**6. Generate Access Tokens**
- Go to "Keys and tokens" tab
- Under "Access Token and Secret", click "Generate"
- Save both the Access Token and Access Token Secret

### Important Notes

- If you change app permissions after generating tokens, you must regenerate the access tokens
- Old tokens will not reflect the new permissions
- The free tier allows 50 tweets per 24 hours, which is sufficient for typical usage

### Common Issues

**403 Forbidden Error**
- Cause: App doesn't have write permissions
- Solution: Ensure "Read and Write" is selected, save, then regenerate access tokens

**401 Unauthorized Error**
- Cause: Incorrect credentials
- Solution: Verify all four credentials are correct and have no extra spaces

**429 Rate Limit Error**
- Cause: Exceeded posting limit
- Solution: The bot includes retry logic. Consider reducing `MAX_POSTS_PER_RUN` if this occurs frequently

## YouTube Data API v3 Setup

You need one credential for YouTube access:

- `YOUTUBE_API_KEY` (API key for YouTube Data API v3)

### Getting YouTube API Key

**URL**: https://console.cloud.google.com

### Step-by-Step Process

**1. Create a Google Cloud Project**
- Click the project dropdown in the top navigation
- Select "New Project"
- Project name: Choose a descriptive name (e.g., "finsure-agent-wire")
- Click "Create"
- Wait approximately 30 seconds for project creation

**2. Enable YouTube Data API v3**
- Use the search bar to find "YouTube Data API v3"
- Click on the API
- Click "Enable"
- Wait for the API to be activated

**3. Create API Key**
- Navigate to "Credentials" from the left sidebar
- Click "Create Credentials"
- Select "API key"
- Copy the generated key

**4. Restrict Key** (Optional but Recommended)
- Click on the API key name
- Under "API restrictions", select "Restrict key"
- Check only "YouTube Data API v3"
- Click "Save"

### Quota Information

The free tier provides:
- 10,000 quota units per day
- Each search request costs 100 units
- Running every 6 hours with 3-4 queries uses approximately 400-500 units per day
- This is well within the free tier limits

### Common Issues

**403 Forbidden Error**
- Cause: API not enabled or quota exceeded
- Solution: Verify the API is enabled and check quota usage

**400 Bad Request Error**
- Cause: Invalid query parameters
- Solution: Check that `YOUTUBE_QUERIES` in `.env` is properly formatted (comma-separated, no quotes)

## Storing Credentials

### Local Development

Create a `.env` file in the project root:

```bash
# X API credentials (required)
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_SECRET=your_access_token_secret_here

# YouTube API (optional)
YOUTUBE_API_KEY=your_youtube_key_here

# Configuration
DRY_RUN=true
LOOKBACK_HOURS=24
MAX_POSTS_PER_RUN=5
MAX_POSTS_PER_DOMAIN=1
MIN_SCORE_THRESHOLD=5.0
```

Important:
- Never commit `.env` to version control
- The file is already listed in `.gitignore`
- Ensure no extra spaces or quotes around values

### GitHub Actions Deployment

For automated deployment via GitHub Actions:

1. Navigate to your repository on GitHub
2. Go to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add each credential as a separate secret:
   - Name: `X_API_KEY`, Value: [your API key]
   - Name: `X_API_SECRET`, Value: [your API secret]
   - Name: `X_ACCESS_TOKEN`, Value: [your access token]
   - Name: `X_ACCESS_SECRET`, Value: [your access token secret]
   - Name: `YOUTUBE_API_KEY`, Value: [your YouTube key] (optional)

The workflow file is already configured to use these secrets.

## RSS Feeds Configuration

RSS feeds don't require API keys. Simply add feed URLs to your `.env` file:

```bash
RSS_FEEDS=https://medium.com/feed/tag/fintech,https://techcrunch.com/feed/
```

### Finding RSS Feeds

Most publications offer RSS feeds. Common patterns:
- Look for `/feed/` or `/rss/` URLs
- Check for RSS icons on websites
- Search: "site:example.com rss"

### Premium Sources

The following sources are already configured:
- Wall Street Journal
- Financial Times
- Reuters
- American Banker
- Insurance Journal
- MIT Technology Review
- Wired
- TechCrunch
- VentureBeat
- CoinDesk

## Credential Validation

Before running the bot, verify:

- [ ] All X API credentials are saved
- [ ] X app has "Read and Write" permissions
- [ ] Access tokens were generated after setting permissions
- [ ] YouTube API key is saved (if using YouTube)
- [ ] No extra spaces or quotes in `.env` file
- [ ] `DRY_RUN=true` for initial testing

## Testing Credentials

Test your setup with:

```bash
python scripts/run_once.py
```

This will validate credentials and attempt to collect news without posting (if `DRY_RUN=true`).

## Security Best Practices

1. Never commit `.env` to version control
2. Use GitHub Secrets for deployment
3. Restrict API keys to only the necessary services
4. Rotate credentials periodically
5. Monitor API usage for unexpected activity
6. Use separate credentials for development and production if possible

## Cost Summary

All required services are free:

| Service | Free Tier | Typical Usage | Cost |
|---------|-----------|---------------|------|
| X API | 50 tweets/24h | 20 tweets/24h | Free |
| YouTube API | 10,000 units/day | 400 units/day | Free |
| RSS Feeds | Unlimited | N/A | Free |

## Support Resources

- **X API Documentation**: https://developer.twitter.com/en/docs
- **YouTube API Documentation**: https://developers.google.com/youtube/v3
- **X API Support**: https://developer.twitter.com/en/support
- **Google Cloud Support**: https://console.cloud.google.com/support

For project-specific issues, consult the main [README.md](./README.md) or [SETUP.md](./SETUP.md).
